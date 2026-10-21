import concurrent.futures
import contextlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

SKILL = Path(__file__).resolve().parents[1] / "skills" / "self-learning"
sys.path.insert(0, str(SKILL))
import evidence
import install
import learning
import reflection


class LearningTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="learning-test-")
        self.root = Path(self.temp.name).resolve()
        self.store = learning.Store(self.root / "state")
        self.project = self.root / "project"
        self.project.mkdir()
        self.project_id = learning.project_identity(self.project)[0]

    def tearDown(self):
        self.temp.cleanup()

    def transcript(self, host, sid, text="Please investigate the slow Danger CI duration again."):
        path = self.root / (host + sid + ".jsonl")
        if host == "claude":
            rows = [
                {"type": "user", "sessionId": sid, "message": {"role": "user", "content": text}},
                {"type": "assistant", "sessionId": sid, "message": {"content": [
                    {"type": "tool_use", "name": "Bash", "input": {"command": "gh run view 123"}}]}},
                {"type": "user", "sessionId": sid, "message": {"role": "user", "content": [
                    {"type": "tool_result", "content": "Danger completed in 420 seconds; investigation verified."}]}},
            ]
        else:
            rows = [
                {"type": "session_meta", "payload": {"id": sid}},
                {"type": "response_item", "payload": {"type": "message", "role": "user",
                    "content": [{"type": "input_text", "text": text}]}},
                {"type": "response_item", "payload": {"type": "function_call", "name": "exec_command",
                    "arguments": '{"cmd":"gh run view 456"}'}},
                {"type": "response_item", "payload": {"type": "function_call_output",
                    "output": "Danger completed in 390 seconds; investigation verified."}},
            ]
        path.write_text("".join(json.dumps(r) + "\n" for r in rows))
        return {"session_id": sid, "cwd": str(self.project), "transcript_path": str(path)}

    def gather(self):
        for host, sid in (("claude", "one"), ("codex", "two")):
            self.store.enqueue(host, self.transcript(host, sid))
        while True:
            job = self.store.queue.claim_next("test")
            if job is None:
                break
            self.store.collect(job)
            self.store.queue.complete(job["id"], "test", {
                "status": "nothing_to_save", "skills": [], "candidates": [], "summary": "fixture"})
        return self.store.bundle(self.project_id)

    def result(self, bundle):
        users = {}
        tool = None
        for ev in bundle["evidence"]:
            if ev["role"] == "user":
                users[ev["session"]] = ev
            if ev["role"] == "tool_result":
                tool = ev
        refs = [{"id": e["id"], "quote": e["text"][:100]} for e in users.values()]
        common = {"slug": "danger-duration", "title": "Investigate Danger durations",
                  "description": "Use when investigating recurring Danger CI delays.",
                  "body": "Inspect job durations and compare repeated runs before proposing a fix.",
                  "evidence": refs + [{"id": tool["id"], "quote": tool["text"]}]}
        proposal = dict(common, slug="danger-monitor", title="Monitor Danger duration regressions",
                        body="Monitor durations against a baseline. Notify on regressions; "
                             "measure whether manual CI checking decreases.")
        return {"skills": [common], "proposals": [proposal], "outcomes": []}

    def test_both_transcript_formats_and_snapshot_cutoff(self):
        for host in ("claude", "codex"):
            payload = self.transcript(host, host)
            path = Path(payload["transcript_path"])
            cutoff = evidence.row_count(path)
            path.write_text(path.read_text() + json.dumps({"type": "user", "message": {
                "content": "DO NOT READ FUTURE ROWS"}}) + "\n")
            rows = evidence.read_evidence(path, cutoff, host, host + ":" + host)
            self.assertEqual({r["role"] for r in rows}, {"user", "tool_call", "tool_result"})
            self.assertNotIn("FUTURE", json.dumps(rows))

    def test_long_trace_keeps_user_intent_and_redacts_secrets(self):
        payload = self.transcript("claude", "long", "Check Danger with api_key=123456789secret")
        path = Path(payload["transcript_path"])
        with path.open("a") as out:
            for _ in range(400):
                out.write(json.dumps({"type": "assistant", "message": {"content": "Polling status"}}) + "\n")
        rows = evidence.read_evidence(path, 1000, "claude", "claude:long")
        self.assertLessEqual(len(rows), 240)
        self.assertIn("Check Danger", json.dumps(rows))
        self.assertNotIn("123456789secret", json.dumps(rows))

    def test_wrong_session_and_symlink_are_rejected(self):
        p = self.transcript("codex", "actual")
        with self.assertRaises(ValueError):
            evidence.read_evidence(p["transcript_path"], 10, "codex", "codex:wrong")
        link = self.root / "linked.jsonl"
        link.symlink_to(p["transcript_path"])
        with self.assertRaises(OSError):
            evidence.row_count(link)

    def test_queue_dedup_and_concurrent_hooks(self):
        payload = self.transcript("claude", "same")
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
            list(pool.map(lambda _: self.store.enqueue("claude", payload), range(12)))
        self.assertEqual(self.store.queue.status()["counts"]["pending"], 1)
        path = Path(payload["transcript_path"])
        with path.open("a") as out:
            out.write(json.dumps({"type": "assistant", "message": {"content": "New result"}}) + "\n")
        self.store.enqueue("claude", payload)
        job = self.store.queue.claim_next("one")
        self.assertEqual(job["transcript_rows"], 4)
        self.assertIsNone(self.store.queue.claim_next("two"))
        self.assertTrue(self.store.queue.acquire_worker_lease("one"))
        self.assertFalse(self.store.queue.acquire_worker_lease("two"))
        self.store.queue.release_worker_lease("one")

    def test_single_session_cannot_trigger_model(self):
        self.store.enqueue("claude", self.transcript("claude", "single"))
        with patch.object(reflection, "run_model") as model:
            learning.worker(self.store)
        model.assert_not_called()
        self.assertEqual(self.store.queue.status()["counts"]["done"], 1)

    def test_cross_host_learning_recall_and_proposal_notification(self):
        bundle = self.gather()
        result = reflection.apply_result(self.store, bundle, self.result(bundle))
        self.assertEqual(result["status"], "changed")
        first = self.store.context(self.project_id, "Danger CI duration", "codex:next")
        self.assertIn("Learned procedure", first)
        self.assertIn("Monitor Danger", first)
        second = self.store.context(self.project_id, "Danger CI duration", "claude:next")
        self.assertIn("Learned procedure", second)
        self.assertNotIn("New workflow improvement proposal", second)
        self.assertEqual(self.store.context("unrelated-project", "Danger"), "")
        self.assertEqual(len(list((self.store.root / "skills").rglob("SKILL.md"))), 1)

    def test_all_output_validated_before_any_write(self):
        bundle = self.gather()
        for change in ("bad_quote", "one_session", "unsafe_path"):
            response = self.result(bundle)
            item = response["proposals"][0]
            if change == "bad_quote":
                item["evidence"][0] = {"id": item["evidence"][0]["id"], "quote": "invented source text"}
            elif change == "one_session":
                item["evidence"] = [item["evidence"][0], item["evidence"][0]]
            else:
                item["slug"] = "../../outside"
            with self.assertRaises(ValueError):
                reflection.apply_result(self.store, bundle, response)
            with self.store.db() as db:
                self.assertEqual(db.execute("SELECT COUNT(*) FROM artifacts").fetchone()[0], 0)

    def test_recall_requires_task_terms_and_does_not_consume_unrelated_proposals(self):
        bundle = self.gather()
        reflection.apply_result(self.store, bundle, self.result(bundle))
        for prompt in ("Please investigate the login timeout", "Help me compare two button colors", ""):
            self.assertEqual(self.store.context(self.project_id, prompt, "claude:unrelated"), "")
        relevant = self.store.context(self.project_id, "Danger CI duration", "codex:relevant")
        self.assertIn("Learned procedure", relevant)
        self.assertIn("New workflow improvement proposal", relevant)

    def test_exact_citation_can_rebind_only_to_unique_record_in_same_session(self):
        bundle = self.gather()
        sources = {e["id"]: e for e in bundle["evidence"]}
        user = next(e for e in bundle["evidence"] if e["role"] == "user")
        tool = next(e for e in bundle["evidence"] if e["session"] == user["session"] and e["role"] == "tool_result")
        ref = {"id": user["id"], "quote": tool["text"]}
        self.assertEqual(reflection.reference(ref, sources)["id"], tool["id"])
        self.assertEqual(ref["id"], tool["id"])
        other = next(e for e in bundle["evidence"] if e["session"] != user["session"] and e["role"] == "tool_result")
        with self.assertRaises(ValueError):
            reflection.reference({"id": user["id"], "quote": other["text"]}, sources)
        sources["duplicate"] = dict(tool, id="duplicate")
        with self.assertRaises(ValueError):
            reflection.reference({"id": user["id"], "quote": tool["text"]}, sources)

    def test_dismissed_proposals_stay_dismissed_and_harmful_skills_withdrawn(self):
        bundle = self.gather()
        response = self.result(bundle)
        reflection.apply_result(self.store, bundle, response)
        identifier = self.project_id + ":proposal:danger-monitor"
        with self.store.db() as db:
            db.execute("UPDATE artifacts SET status='dismissed' WHERE id=?", (identifier,))
        reflection.apply_result(self.store, bundle, response)
        skill = self.project_id + ":skill:danger-duration"
        self.store.feedback(skill, "harmful", "This procedure was wrong for our CI setup.", "user-result")
        reflection.apply_result(self.store, bundle, response)
        self.assertEqual(self.store.context(self.project_id, "Danger"), "")
        with self.store.db() as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM revisions").fetchone()[0], 2)

    def test_automatic_feedback_requires_later_user_evidence_and_delivery(self):
        bundle = self.gather()
        reflection.apply_result(self.store, bundle, self.result(bundle))
        skill = self.project_id + ":skill:danger-duration"
        user = next(e for e in bundle["evidence"] if e["role"] == "user")
        response = {"skills": [], "proposals": [], "outcomes": [{
            "artifact": skill, "verdict": "harmful",
            "evidence": {"id": user["id"], "quote": user["text"]}}]}
        bundle = self.store.bundle(self.project_id)
        with self.assertRaises(ValueError):
            reflection.apply_result(self.store, bundle, response)
        self.store.context(self.project_id, "Danger", user["session"], user["row_number"])
        with self.assertRaises(ValueError):
            reflection.apply_result(self.store, bundle, response)
        self.store.context(self.project_id, "Danger", user["session"], user["row_number"] + 1)
        with self.assertRaises(ValueError):
            reflection.apply_result(self.store, bundle, response)
        later = dict(user, id="ev-later-feedback", row_number=user["row_number"]+2,
                     text="The learned Danger procedure failed to account for queue time.")
        with self.store.db() as db:
            db.execute("INSERT INTO evidence VALUES(?,?,?,?,?,?,?)",
                       (later["id"], later["session"], self.project_id,
                        later["row_number"], "user", later["text"], time.time()))
        response["outcomes"][0]["evidence"] = {"id": later["id"], "quote": later["text"]}
        bundle = self.store.bundle(self.project_id)
        reflection.apply_result(self.store, bundle, response)
        self.assertNotIn("Learned procedure", self.store.context(self.project_id, "Danger"))

    def test_budget_shared_by_hosts_and_failed_attempts_count(self):
        self.store.config["max_calls_per_day"] = 1
        self.assertIsNotNone(self.store.reserve_run(self.project_id))
        self.assertIsNone(self.store.reserve_run("another-project"))

    def test_proposal_feedback_closes_the_loop_and_informs_later_reflection(self):
        bundle = self.gather()
        reflection.apply_result(self.store, bundle, self.result(bundle))
        identifier = self.project_id + ":proposal:danger-monitor"
        self.store.context(self.project_id, "Danger", "codex:two", 4)
        note = "The new Danger monitor reduced the number of manual CI checks I needed."
        with self.store.db() as db:
            db.execute("INSERT INTO evidence VALUES(?,?,?,?,?,?,?)",
                       ("ev-monitor-result", "codex:two", self.project_id, 5, "user", note, time.time()))
        bundle = self.store.bundle(self.project_id)
        reflection.apply_result(self.store, bundle, {"skills": [], "proposals": [], "outcomes": [{
            "artifact": identifier, "verdict": "helpful",
            "evidence": {"id": "ev-monitor-result", "quote": note}}]})
        later = self.store.bundle(self.project_id)
        proposal = next(a for a in later["artifacts"] if a["id"] == identifier)
        self.assertEqual(proposal["status"], "helpful")
        self.assertEqual(proposal["reported_outcomes"][0]["verdict"], "helpful")
        self.assertIn("reduced", proposal["reported_outcomes"][0]["note"])

    def test_abandoned_job_recovery_preserves_work_and_attempt_count(self):
        self.store.enqueue("claude", self.transcript("claude", "recover"))
        job = self.store.queue.claim_next("dead-worker")
        with patch("upstream_queue._pid_matches_identity", return_value=False):
            self.assertEqual(self.store.queue.recover_expired_jobs(), 1)
        with self.store.db() as db:
            db.execute("UPDATE review_jobs SET available_at=0 WHERE id=?", (job["id"],))
        recovered = self.store.queue.claim_next("replacement")
        self.assertEqual(recovered["id"], job["id"])
        self.assertEqual(recovered["attempts"], 2)
        self.assertEqual(recovered["transcript_path"], job["transcript_path"])

    def test_runner_timeout_leaves_retryable_job_and_no_artifacts(self):
        fake = self.root / "slow-codex"
        fake.write_text("#!" + sys.executable + "\nimport time\ntime.sleep(30)\n")
        fake.chmod(0o700)
        self.store.enqueue("claude", self.transcript("claude", "slow-one"))
        self.store.enqueue("codex", self.transcript("codex", "slow-two"))
        self.store.config.update(engine="codex", timeout_seconds=1)
        started = time.monotonic()
        with patch.dict(os.environ, {"AGENTIC_LEARNING_CODEX_BIN": str(fake)}):
            learning.worker(self.store)
        self.assertLess(time.monotonic()-started, 5)
        self.assertEqual(self.store.queue.status()["counts"]["pending"], 1)
        with self.store.db() as db:
            self.assertEqual(db.execute("SELECT status FROM runs").fetchone()[0], "failed")
            self.assertEqual(db.execute("SELECT COUNT(*) FROM artifacts").fetchone()[0], 0)

    def test_installed_hooks_speak_native_protocol_for_both_hosts(self):
        home = self.root / "hook-home"
        install.install(home, self.store.root)
        with patch.dict(os.environ, {"AGENTIC_LEARNING_NO_SPAWN": "1"}):
            for host in ("claude", "codex"):
                payload = self.transcript(host, "hook-" + host)
                payload["hook_event_name"] = "Stop"
                command = install.hook_config(host, self.store.root)["Stop"][0]["hooks"][0]["command"]
                import shlex
                import subprocess
                result = subprocess.run(shlex.split(command), input=json.dumps(payload),
                                        capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout, "")
        self.assertEqual(self.store.queue.status()["counts"]["pending"], 2)
        bundle = self.gather()
        reflection.apply_result(self.store, bundle, self.result(bundle))
        for host in ("claude", "codex"):
            payload = self.transcript(host, "recall-" + host)
            payload.update(hook_event_name="UserPromptSubmit", prompt="Danger CI duration")
            command = install.hook_config(host, self.store.root)["UserPromptSubmit"][0]["hooks"][0]["command"]
            with patch.dict(os.environ, {"AGENTIC_LEARNING_NO_SPAWN": "1"}):
                result = subprocess.run(shlex.split(command), input=json.dumps(payload),
                                        capture_output=True, text=True)
            context = json.loads(result.stdout)["hookSpecificOutput"]
            self.assertEqual(context["hookEventName"], "UserPromptSubmit")
            self.assertIn("Learned procedure", context["additionalContext"])

    def test_install_idempotent_preserves_other_hooks_and_uninstalls_only_owned(self):
        home = self.root / "home"
        target = home / ".claude/settings.json"
        target.parent.mkdir(parents=True)
        target.write_text(json.dumps({"theme": "dark", "hooks": {
            "Stop": [{"hooks": [{"type": "command", "command": "other-tool"}]}]}}))
        install.install(home, self.root / "installed")
        first = target.read_text()
        install.install(home, self.root / "installed")
        self.assertEqual(first, target.read_text())
        self.assertTrue((home / ".agents/skills/self-learning").is_symlink())
        install.install(home, self.root / "installed", remove=True)
        current = json.loads(target.read_text())
        self.assertEqual(current["theme"], "dark")
        self.assertEqual(current["hooks"]["Stop"][0]["hooks"][0]["command"], "other-tool")
        self.assertEqual(len(current["hooks"]["Stop"]), 1)
        self.assertFalse((home / ".agents/skills/self-learning").exists())
        install.install(home, self.root / "installed")
        self.assertTrue(json.loads((self.root / "installed/config.json").read_text())["enabled"])

    def test_hook_errors_fail_open_and_worker_recursion_is_suppressed(self):
        with patch.dict(os.environ, {"AGENTIC_LEARNING_WORKER": "1"}), patch.object(learning, "launch_worker") as launch:
            learning.hook(self.store, "codex", "capture", {})
            launch.assert_not_called()
        with patch.object(sys, "argv", ["learning.py", "--state-dir", str(self.store.root),
                                      "hook", "--host", "codex", "--event", "capture"]), \
                patch.object(sys, "stdin", io.StringIO("{}")), contextlib.redirect_stderr(io.StringIO()):
            learning.main()

    def test_real_worker_protocol_with_fake_codex_process(self):
        fake = self.root / "codex"
        fake.write_text("#!" + sys.executable + "\n" + """
import json,sys
lines = sys.stdin.read().splitlines()
bundle = json.loads(next(line for line in lines if line.startswith('{"project":')))
users = {}
tool = None
for ev in bundle["evidence"]:
    if ev["role"] == "user": users[ev["session"]] = ev
    if ev["role"] == "tool_result": tool = ev
refs = [{"id":e["id"],"quote":e["text"][:100]} for e in users.values()]
refs.append({"id":tool["id"],"quote":tool["text"]})
item = {"slug":"danger-triage","title":"Triage Danger CI","description":"Investigate CI durations.",
        "body":"Compare observed job durations across runs.", "evidence":refs}
output = sys.argv[sys.argv.index("--output-last-message")+1]
open(output,"w").write(json.dumps({"skills":[item],"proposals":[],"outcomes":[]}))
""")
        fake.chmod(0o700)
        self.store.enqueue("claude", self.transcript("claude", "process-one"))
        self.store.enqueue("codex", self.transcript("codex", "process-two"))
        self.store.config["engine"] = "codex"
        with patch.dict(os.environ, {"AGENTIC_LEARNING_CODEX_BIN": str(fake)}):
            learning.worker(self.store)
        self.assertEqual(self.store.queue.status()["counts"]["done"], 2)
        self.assertIn("Triage", (self.store.root / "skills" / self.project_id / "danger-triage/SKILL.md").read_text())
        with self.store.db() as db:
            self.assertEqual(db.execute("SELECT status FROM runs").fetchone()[0], "done")


if __name__ == "__main__":
    unittest.main()
