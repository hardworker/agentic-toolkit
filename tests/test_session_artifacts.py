import concurrent.futures
import hashlib
import importlib.util
import json
import os
import re
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from urllib.parse import unquote
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/self-learning"))
import learning
import install

spec = importlib.util.spec_from_file_location("planning_sessions", ROOT / "skills/grounded-plan/sessions.py")
sessions = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sessions)


class Fixtures(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="session-artifacts-")
        self.root = Path(self.temp.name).resolve()
        self.library = self.root / "library"
        self.project = self.root / "project"
        self.project.mkdir()

    def tearDown(self):
        self.temp.cleanup()

    def cli(self, *args, project=None, check=True):
        result = subprocess.run([sys.executable, "-B", str(ROOT / "skills/grounded-plan/sessions.py"),
                                 "--store", str(self.library), "--project", str(project or self.project),
                                 *args], capture_output=True, text=True, check=check)
        return json.loads(result.stdout) if check else result

    def create(self, key="task", title="Release reliability", source="codex:a", project=None):
        return self.cli("create", "--title", title, "--key", key, "--source", source, project=project)


class SessionArtifactsTest(Fixtures):
    def test_identity_continuation_and_independent_title(self):
        first = self.create()
        opened = self.cli("open", "--source", "codex:a")
        self.assertEqual(first["id"], opened["id"])
        renamed_chat = self.cli("update", "--session", first["id"], "--source", "codex:a",
                                "--source-title", "A different chat title")
        self.assertEqual(renamed_chat["title"], first["title"])
        self.assertEqual(renamed_chat["sources"][0]["title"], "A different chat title")
        renamed = self.cli("update", "--session", first["entry"], "--title", "Safer releases")
        self.assertEqual(renamed["id"], first["id"])
        self.assertEqual(renamed["entry"], first["entry"])
        self.assertEqual(renamed["title"], "Safer releases")
        second = self.create("another-topic")
        self.assertNotEqual(first["id"], second["id"])
        self.assertNotEqual(first["entry"], second["entry"])
        self.assertNotEqual(self.cli("open", "--source", "codex:a", check=False).returncode, 0)
        self.assertEqual(self.cli("open", "--session", first["id"])["id"], first["id"])

    def test_scope_collision_sanitization_and_native_host_identity(self):
        first = self.create(title="../../Release / reliability ✨")
        other = self.root / "another-project"
        other.mkdir()
        second = self.create(title="../../Release / reliability ✨", project=other)
        self.assertNotEqual(first["entry"], second["entry"])
        self.assertTrue(Path(first["entry"]).is_relative_to(self.library / "sessions"))
        self.assertNotEqual(self.cli("open", "--session", first["id"], project=other, check=False).returncode, 0)
        self.assertNotEqual(self.cli("open", "--source", "claude:a", check=False).returncode, 0)
        self.assertNotEqual(self.cli("open", "--source", "a", check=False).returncode, 0)

    def test_worktrees_share_project_scope(self):
        hooks = self.root / "empty-hooks"
        hooks.mkdir()
        git = ["git", "-c", "commit.gpgsign=false", "-c", "core.hooksPath=" + str(hooks)]
        subprocess.run(git + ["init", "-q", str(self.project)], check=True)
        subprocess.run(git + ["-C", str(self.project), "-c", "user.name=Fixture", "-c",
                              "user.email=fixture@example.invalid", "commit", "-qm", "fixture", "--allow-empty"], check=True)
        worktree = self.root / "worktree"
        subprocess.run(git + ["-C", str(self.project), "worktree", "add", "--detach", "-q", str(worktree)], check=True)
        first = self.create()
        self.assertEqual(self.cli("open", "--source", "codex:a", project=worktree)["id"], first["id"])

    def test_concurrent_creation_sources_and_link_additions(self):
        def create(i):
            return self.create(source="codex:" + str(i))
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
            created = list(pool.map(create, range(12)))
        self.assertEqual(len({e["id"] for e in created}), 1)
        identifier = created[0]["id"]
        def attach(i):
            path = self.root / (str(i) + ".md")
            path.write_text("Evidence " + str(i))
            return self.cli("attach", "--session", identifier, "--path", str(path), "--kind", "evidence")
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
            list(pool.map(attach, range(12)))
        final = self.cli("open", "--session", identifier)
        self.assertEqual(len(final["sources"]), 12)
        self.assertEqual(len(final["links"]), 12)
        self.assertEqual(len(list((self.library / "sessions").iterdir())), 1)
        self.assertIn(identifier, (self.library / "index.md").read_text())
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            distinct = list(pool.map(lambda i: self.create(key="separate-" + str(i)), range(4)))
        self.assertEqual(len({e["id"] for e in distinct}), 4)
        for data in distinct:
            self.assertIn(data["id"], (self.library / "index.md").read_text())
        self.assertEqual(len(list((self.library / "sessions").iterdir())), 5)

    def test_new_plans_external_destinations_and_legacy_pilot(self):
        legacy = self.library / "records" / "old-plan.md"
        legacy.parent.mkdir(parents=True)
        legacy.write_text("# Old plan\n\nID: legacy-stable\n\nOriginal expectations and decisions.\n")
        original = legacy.read_bytes()
        data = self.create()
        self.assertEqual(list(Path(data["entry"]).parent.iterdir()), [Path(data["entry"])])
        self.cli("attach", "--session", data["id"], "--path", str(legacy), "--kind", "plan")
        content = self.root / "content.md"
        content.write_text("Current direction.\n\n## Outcomes\n\nPending — no results recorded.\n")
        result = self.cli("plan", "--session", data["id"], "--title", "Rollout", "--content-file", str(content))
        new = next(link for link in result["links"] if link["id"] != "legacy-stable")
        self.assertEqual(Path(new["path"]).parent.name, "plans")
        external = self.root / "explicit.md"
        self.cli("plan", "--session", data["id"], "--title", "Monitoring", "--content-file", str(content),
                 "--destination", str(external))
        before = external.read_bytes()
        failed = self.cli("plan", "--session", data["id"], "--title", "Monitoring", "--content-file", str(content),
                          "--destination", str(external), check=False)
        self.assertNotEqual(failed.returncode, 0)
        self.assertEqual(external.read_bytes(), before)
        self.assertEqual(legacy.read_bytes(), original)
        self.assertIn("legacy-stable", (self.library / "index.md").read_text())
        self.assertIn("legacy-stable", Path(data["entry"]).read_text())
        self.assertEqual(self.cli("find", "--id", "legacy-stable")["paths"], [str(legacy)])
        self.assertEqual(self.cli("find", "--id", new["id"])["paths"], [new["path"]])
        self.assertNotEqual(self.cli("plan", "--session", data["id"], "--title", "Duplicate",
                                    "--content-file", str(content), "--id", "legacy-stable", check=False).returncode, 0)
        copy = self.root / "competing.md"
        copy.write_bytes(original)
        self.assertNotEqual(self.cli("attach", "--session", data["id"], "--path", str(copy), "--kind", "plan",
                                    check=False).returncode, 0)

    def test_root_overrides_and_index_failure_preserves_session(self):
        with patch.dict(os.environ, {"GROUNDED_PLAN_HOME": str(self.library)}):
            self.assertEqual(sessions.library_root(), self.library)
            self.assertEqual(sessions.library_root(str(self.root)), self.root)
        with patch.dict(os.environ, {"GROUNDED_PLAN_HOME": ""}):
            self.assertEqual(sessions.library_root("relative"), (Path.cwd() / "relative").resolve())
        data = self.create()
        with sessions.locked(self.library), patch.object(sessions, "index", side_effect=OSError("fixture")):
            data["summary"] = "Updated independently of index."
            result = sessions.save(self.library, data)
        self.assertFalse(result["indexed"])
        self.assertEqual(sessions.entry(data["entry"])["summary"], data["summary"])
        self.cli("index")
        self.assertIn(data["summary"], (self.library / "index.md").read_text())

    def test_symlink_entry_cannot_redirect_planning_writes(self):
        data = self.create()
        path = Path(data["entry"])
        outside = self.root / "outside.md"
        outside.write_bytes(path.read_bytes())
        path.unlink()
        path.symlink_to(outside)
        original = outside.read_bytes()
        self.assertNotEqual(self.cli("update", "--session", data["id"], "--title", "Wrong", check=False).returncode, 0)
        self.assertEqual(outside.read_bytes(), original)

    def test_implicit_plan_directory_cannot_redirect_writes(self):
        data = self.create()
        outside = self.root / "external-owner"
        outside.mkdir()
        (Path(data["entry"]).parent / "plans").symlink_to(outside, target_is_directory=True)
        draft = self.root / "draft.md"
        draft.write_text("Draft")
        result = self.cli("plan", "--session", data["id"], "--title", "Redirected", "--content-file", str(draft), check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(list(outside.iterdir()), [])


class DiscoveryTest(Fixtures):
    def fixture(self):
        store = learning.Store(self.root / "learning")
        project = learning.project_identity(self.project)[0]
        with store.db() as db:
            for source in ("codex:a", "claude:b", "codex:c"):
                transcript = self.root / (source + ".jsonl")
                transcript.write_text("fixture")
                db.execute("INSERT INTO sessions VALUES(?,?,?,?,?,?)",
                           (source, project, str(self.project), source.split(":")[0], str(transcript), 1))
                db.execute("INSERT INTO evidence VALUES(?,?,?,?,?,?,?)",
                           (source + ":ev", source, project, 9, "user", "Useful evidence", 1))
        identifier = store.publish(project, "skill", {"slug": "release-checks", "title": "Release checks",
            "description": "Release checks", "body": "Inspect releases", "evidence": [
                {"id": "codex:a:ev", "quote": "Useful"}, {"id": "claude:b:ev", "quote": "Useful"}]})
        with store.db() as db:
            db.execute("INSERT INTO deliveries VALUES(?,?,?,?,?)", (identifier, 1, "codex:c", 4, 2))
        store.feedback(identifier, "helpful", "Worked in C", "codex:c:ev")
        store.feedback(identifier, "helpful", "Manual feedback has no session", "user-fixture")
        return store, project, identifier

    def test_relationships_manual_feedback_scope_and_no_receipts(self):
        store, project, identifier = self.fixture()
        def snapshot():
            return {str(p.relative_to(store.root)): hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in store.root.rglob("*") if p.is_file()}
        before = snapshot()
        with patch.object(learning, "Store", side_effect=AssertionError("no store initialization")), \
                patch.object(learning, "launch_worker", side_effect=AssertionError("no worker")):
            for source, expected in (("codex:a", ["supporting-evidence"]),
                                     ("claude:b", ["supporting-evidence"]),
                                     ("codex:c", ["delivery", "reported-outcome"])):
                listing = learning.discover(store.root, project, [source])
                self.assertEqual(len(listing["artifacts"]), 1)
                artifact = listing["artifacts"][0]
                self.assertEqual([r["kind"] for r in artifact["relationships"]], expected)
                self.assertEqual(artifact["id"], identifier)
                manual = next(o for o in artifact["reported_outcomes"] if o["evidence_id"] == "user-fixture")
                self.assertIsNone(manual["session"])
            self.assertEqual(learning.discover(store.root, "other-project", ["codex:a"], [identifier])["artifacts"], [])
            self.assertEqual(learning.discover(store.root, project, ["codex:unknown"])["artifacts"], [])
        self.assertEqual(snapshot(), before)

    def test_historical_evidence_survives_revision_and_missing_sources(self):
        store, project, identifier = self.fixture()
        store.publish(project, "skill", {"slug": "release-checks", "title": "Revised checks",
            "description": "Revised", "body": "Inspect releases more closely", "evidence": [
                {"id": "codex:c:ev", "quote": "Useful"}, {"id": "lost", "quote": "Unavailable"}]})
        (self.root / "codex:a.jsonl").unlink()
        artifact = learning.discover(store.root, project, ["codex:a"])["artifacts"][0]
        self.assertEqual(artifact["revision"], 2)
        self.assertEqual(artifact["relationships"], [{"kind": "supporting-evidence", "sessions": ["codex:a"]}])
        self.assertFalse(next(e for e in artifact["evidence"] if e["id"] == "codex:a:ev")["available"])
        missing = next(e for e in artifact["evidence"] if e["id"] == "lost")
        self.assertIsNone(missing["session"])
        self.assertFalse(missing["available"])

    def test_missing_store_listing_creates_nothing(self):
        missing = self.root / "missing"
        listing = learning.discover(missing, "project", ["codex:a"])
        self.assertFalse(listing["available"])
        self.assertFalse(missing.exists())
        result = subprocess.run([sys.executable, "-B", str(ROOT / "skills/self-learning/learning.py"),
                                 "--state-dir", str(missing), "discover", "--project", str(self.project)],
                                capture_output=True, text=True, check=True)
        self.assertFalse(json.loads(result.stdout)["available"])
        self.assertFalse(missing.exists())

    def test_refresh_selected_links_outcomes_missing_files_and_optional_runtime(self):
        store, project, identifier = self.fixture()
        data = self.create(source="codex:c")
        cli = ROOT / "skills/self-learning/learning.py"
        self.cli("refresh", "--session", data["id"], "--learning-cli", str(cli), "--state-dir", str(store.root))
        text = Path(data["entry"]).read_text()
        self.assertIn("delivery: codex:c", text)
        self.assertIn("reported-outcome: codex:c", text)
        self.assertIn("unattributed manual feedback", text)
        artifact = learning.discover(store.root, project)["artifacts"][0]
        # Explicit selection survives changing source matches and discovery failures.
        selected = self.create(key="selected", source="codex:unrelated")
        self.cli("attach", "--session", selected["id"], "--path", artifact["path"], "--kind", "artifact",
                 "--owner", "self-learning", "--id", identifier)
        store.feedback(identifier, "harmful", "Did not help", "user-second")
        Path(artifact["path"]).unlink()
        updated = self.cli("refresh", "--session", selected["id"], "--learning-cli", str(cli), "--state-dir", str(store.root))
        self.assertEqual(updated["links"][0]["id"], identifier)
        self.assertEqual(updated["learning"]["artifacts"][0]["status"], "harmful")
        self.assertFalse(updated["learning"]["artifacts"][0]["available"])
        self.assertIn("unavailable", Path(selected["entry"]).read_text())
        failed = self.cli("refresh", "--session", selected["id"], "--learning-cli", str(self.root / "absent.py"))
        self.assertFalse(failed["learning"]["available"])
        self.assertEqual(failed["links"], updated["links"])
        self.assertEqual(failed["learning"]["artifacts"], updated["learning"]["artifacts"])
        malformed = self.root / "malformed.py"
        malformed.write_text("print(" + repr(json.dumps({"owner": "self-learning", "available": True,
            "refreshed": "now", "database": "fixture", "artifacts": [{}]})) + ")")
        failed = self.cli("refresh", "--session", selected["id"], "--learning-cli", str(malformed))
        self.assertFalse(failed["learning"]["available"])
        self.assertEqual(failed["learning"]["artifacts"], updated["learning"]["artifacts"])

    def test_controlled_existing_work_pilot_links_fresh_work_and_canonical_outcomes(self):
        store, project, identifier = self.fixture()
        legacy = self.library / "records" / "existing.md"
        legacy.parent.mkdir(parents=True)
        legacy.write_text("# Existing plan\n\nID: existing-id\n\nOriginal decisions.\n")
        original = legacy.read_bytes()
        data = self.create(source="codex:c")
        folder = Path(data["entry"]).parent
        evidence = folder / "evidence" / "source-review.md"
        evidence.parent.mkdir()
        evidence.write_text("Decisive fixture evidence: use a reversible rollout gate.")
        outcome = folder / "observed.md"
        outcome.write_text("Observed: links resolve. Product benefit remains unmeasured.")
        draft = self.root / "draft.md"
        draft.write_text("Choose a reversible rollout gate.\n\nOutcomes pending.")
        self.cli("plan", "--session", data["id"], "--title", "Rollout", "--content-file", str(draft))
        for kind, path in (("plan", legacy), ("evidence", evidence), ("outcome", outcome)):
            self.cli("attach", "--session", data["id"], "--kind", kind, "--path", str(path))
        updated = self.cli("refresh", "--session", data["id"], "--learning-cli",
                           str(ROOT / "skills/self-learning/learning.py"), "--state-dir", str(store.root))
        # Index -> entry -> plan/evidence/outcome: two navigation edges, no path reconstruction.
        for entry_path in (self.library / "index.md", Path(data["entry"])):
            for destination in re.findall(r"^- \[.*?\]\((.*?)\)", entry_path.read_text(), re.M):
                self.assertTrue((entry_path.parent / unquote(destination)).resolve().is_file())
        self.assertEqual(self.cli("find", "--id", "existing-id")["paths"], [str(legacy)])
        self.assertEqual(legacy.read_bytes(), original)
        self.assertEqual(updated["learning"]["artifacts"][0]["id"], identifier)
        self.assertEqual(Path(updated["learning"]["artifacts"][0]["path"]).parent.name, "release-checks")
        self.assertEqual({link["kind"] for link in updated["links"]}, {"plan", "evidence", "outcome"})
        self.assertTrue(next(Path(link["path"]) for link in updated["links"]
                             if link["kind"] == "plan" and link["id"] != "existing-id").is_relative_to(folder))

    def test_isolated_installer_copies_discovery_and_preserves_symlink_convention(self):
        home, state = self.root / "home", self.root / "installed"
        install.install(home, state)
        for host in (".claude", ".agents"):
            self.assertEqual((home / host / "skills/self-learning").resolve(), ROOT / "skills/self-learning")
        for name in ("learning.py", "reflection.py", "evidence.py", "upstream_queue.py"):
            self.assertEqual((state / "runtime" / name).read_bytes(), (ROOT / "skills/self-learning" / name).read_bytes())
        before = (state / "learning.sqlite3").read_bytes()
        result = subprocess.run([sys.executable, "-B", str(state / "runtime/learning.py"),
                                 "--state-dir", str(state), "discover", "--project", str(self.project)],
                                capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(result.stdout)["artifacts"], [])
        self.assertEqual((state / "learning.sqlite3").read_bytes(), before)
        install.install(home, state)
        install.install(home, state, remove=True)
        self.assertFalse((home / ".agents/skills/self-learning").is_symlink())


if __name__ == "__main__":
    unittest.main()
