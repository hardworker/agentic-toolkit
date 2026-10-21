"""Bounded headless reflection; the model cannot publish its own output."""
from __future__ import annotations

import json
import os
import re
import shutil
import signal
import subprocess
import tempfile
import threading
from pathlib import Path

from evidence import SECRET

REFERENCE = {
    "type": "object", "additionalProperties": False,
    "properties": {"id": {"type": "string"},
                   "quote": {"type": "string", "minLength": 10, "maxLength": 500}},
    "required": ["id", "quote"],
}
ITEM = {
    "type": "object", "additionalProperties": False,
    "properties": {**{key: {"type": "string"} for key in
                      ("slug", "title", "description", "body")},
                   "evidence": {"type": "array", "items": REFERENCE}},
    "required": ["slug", "title", "description", "body", "evidence"],
}
SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "skills": {"type": "array", "items": ITEM},
        "proposals": {"type": "array", "items": ITEM},
        "outcomes": {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "properties": {"artifact": {"type": "string"},
                           "verdict": {"type": "string", "enum": ["helpful", "harmful"]},
                           "evidence": REFERENCE},
            "required": ["artifact", "verdict", "evidence"]}},
    },
    "required": ["skills", "proposals", "outcomes"],
}


class Heartbeat:
    def __init__(self, queue, owner, job):
        self.queue, self.owner, self.job = queue, owner, job
        self.stop = threading.Event()
        self.lost = False
        self.thread = threading.Thread(target=self.run, daemon=True)

    def beat(self):
        if not self.queue.heartbeat_worker(self.owner) or not self.queue.heartbeat_job(self.job, self.owner):
            self.lost = True

    def run(self):
        while not self.stop.wait(15):
            try:
                self.beat()
            except Exception:
                self.lost = True
                return

    def __enter__(self):
        self.beat()
        self.thread.start()
        return self

    def __exit__(self, *args):
        self.stop.set()
        self.thread.join(2)
        if self.lost:
            raise RuntimeError("reflection lost queue ownership")


def command_for(engine, executable, directory, schema, model=None):
    if engine == "claude":
        args = [
            executable, "-p", "--safe-mode", "--tools", "",
            "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}',
            "--settings", '{"disableAllHooks":true}', "--permission-mode", "dontAsk",
            "--disable-slash-commands", "--no-session-persistence",
            "--output-format", "json", "--json-schema", json.dumps(SCHEMA),
            "--max-budget-usd", "1",
        ]
    else:
        args = [
            executable, "exec", "--ignore-user-config", "--ignore-rules",
            "--ephemeral", "--skip-git-repo-check", "--sandbox", "read-only",
            "--cd", str(directory), "--output-schema", str(schema),
            "--output-last-message", str(directory / "result.json"), "--color", "never",
        ]
        for name in ("hooks", "shell_tool", "multi_agent", "apps", "plugins", "memories",
                     "browser_use", "computer_use", "image_generation", "workspace_dependencies",
                     "view_image", "code_mode", "code_mode_host"):
            args.extend(["-c", "features." + name + "=false"])
        args.extend(["-c", "features.skip_host_skill_discovery=true",
                     "-c", "web_search=\"disabled\"", "-c", "mcp_servers={}"])
    if model:
        args.extend(["--model", model])
    return args


def run_model(store, bundle, host):
    engine = store.config["engine"] if store.config["engine"] != "auto" else host
    binary = (os.environ.get("AGENTIC_LEARNING_" + engine.upper() + "_BIN")
              or store.config[engine + "_bin"] or shutil.which(engine))
    if not binary:
        raise RuntimeError(engine + " CLI is unavailable")
    prompt = Path(__file__).with_name("reflection-prompt.md").read_text()
    boundary = os.urandom(16).hex()
    prompt += ("\n\nUntrusted evidence boundary " + boundary + ":\n" +
               json.dumps(bundle, ensure_ascii=False) + "\nEnd evidence " + boundary)
    env = dict(os.environ, AGENTIC_LEARNING_WORKER="1")
    env.pop("CLAUDECODE", None)
    env.pop("CLAUDE_CODE_ENTRYPOINT", None)
    with tempfile.TemporaryDirectory(prefix="agentic-learning-") as scratch:
        directory = Path(scratch).resolve()
        schema = directory / "schema.json"
        schema.write_text(json.dumps(SCHEMA))
        args = command_for(engine, binary, directory, schema, store.config["model"])
        with (directory / "stdout").open("w+") as out, (directory / "stderr").open("w+") as err:
            process = subprocess.Popen(
                args, stdin=subprocess.PIPE, stdout=out, stderr=err, text=True,
                env=env, cwd=directory, start_new_session=True)
            try:
                process.communicate(prompt, timeout=store.config["timeout_seconds"])
            except BaseException:
                # Kill the whole headless process group, not just its launcher.
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait()
                raise
            if process.returncode:
                raise RuntimeError(engine + " reflection exited with code " + str(process.returncode) +
                                   "; check CLI authentication and supported flags")
            if engine == "codex":
                result = directory / "result.json"
                if not result.exists() or result.stat().st_size > 100000:
                    raise ValueError("Codex returned no bounded structured result")
                return json.loads(result.read_text())
            out.seek(0)
            envelope = json.loads(out.read(100001))
            if envelope.get("is_error"):
                raise RuntimeError("Claude reported a reflection error")
            answer = envelope.get("structured_output")
            if answer is None:
                answer = json.loads(envelope.get("result", ""))
            return answer


def reference(value, evidence):
    if not isinstance(value, dict) or set(value) != {"id", "quote"}:
        raise ValueError("invalid evidence reference")
    ev = evidence.get(value["id"])
    quote = value["quote"]
    if not ev or not isinstance(quote, str) or not 10 <= len(quote) <= 500:
        raise ValueError("evidence quote does not match supplied source")
    if quote not in ev["text"]:
        # Repair only a uniquely resolvable citation within the named source session.
        matches = [r for r in evidence.values() if r["session"] == ev["session"] and quote in r["text"]]
        if len(matches) != 1:
            raise ValueError("evidence quote does not match supplied source")
        ev = matches[0]
        value["id"] = ev["id"]
    return ev


def validate_item(item, kind, evidence):
    if not isinstance(item, dict) or set(item) != set(ITEM["required"]):
        raise ValueError("invalid artifact shape")
    if not isinstance(item["slug"], str) or not re.fullmatch(r"[a-z][a-z0-9-]{2,63}", item["slug"]):
        raise ValueError("invalid artifact slug")
    for key, limit in (("title", 160), ("description", 200), ("body", 5000 if kind == "skill" else 3000)):
        text = item[key]
        if not isinstance(text, str) or not text.strip() or len(text) > limit or SECRET.search(text):
            raise ValueError("invalid artifact " + key)
    if item["body"].lstrip().startswith("---"):
        raise ValueError("skill body may not contain frontmatter")
    refs = item["evidence"]
    if not isinstance(refs, list) or not 2 <= len(refs) <= 12:
        raise ValueError("artifact needs bounded independent evidence")
    records = [reference(r, evidence) for r in refs]
    if len({r["session"] for r in records if r["role"] == "user"}) < 2:
        raise ValueError("artifact needs user evidence from two independent sessions")
    if kind == "skill" and not any(r["role"] == "tool_result" for r in records):
        raise ValueError("skill needs observed tool evidence")


def apply_result(store, bundle, response):
    if not isinstance(response, dict) or set(response) != {"skills", "proposals", "outcomes"}:
        raise ValueError("invalid reflection result")
    evidence = {ev["id"]: ev for ev in bundle["evidence"]}
    existing = {a["id"] for a in bundle["artifacts"]}
    for key in response:
        if not isinstance(response[key], list) or len(response[key]) > 3:
            raise ValueError("reflection output exceeds artifact limit")
    for key, kind in (("skills", "skill"), ("proposals", "proposal")):
        slugs = set()
        for item in response[key]:
            validate_item(item, kind, evidence)
            if item["slug"] in slugs:
                raise ValueError("duplicate artifact slug")
            slugs.add(item["slug"])
    for outcome in response["outcomes"]:
        if (not isinstance(outcome, dict) or set(outcome) != {"artifact", "verdict", "evidence"}
                or outcome["artifact"] not in existing or outcome["verdict"] not in {"helpful", "harmful"}):
            raise ValueError("invalid outcome")
        ev = reference(outcome["evidence"], evidence)
        if ev["role"] != "user":
            raise ValueError("outcome needs explicit user evidence")
        with store.db() as db:
            delivery = db.execute(
                "SELECT 1 FROM deliveries WHERE artifact=? AND session=? AND cutoff<?",
                (outcome["artifact"], ev["session"], ev["row_number"])).fetchone()
        if not delivery:
            raise ValueError("outcome predates delivery")
    # Validate the entire result before any durable mutation.
    skills, proposals = [], []
    for item in response["skills"]:
        identifier = store.publish(bundle["project"], "skill", item)
        skills.append({"name": identifier, "action": "upsert", "backup_id": None})
    for item in response["proposals"]:
        identifier = store.publish(bundle["project"], "proposal", item)
        proposals.append({"name": identifier, "reason": item["description"], "proposed_change": item["body"]})
    for outcome in response["outcomes"]:
        store.feedback(outcome["artifact"], outcome["verdict"], outcome["evidence"]["quote"],
                       outcome["evidence"]["id"])
    return {"status": "changed" if skills or proposals or response["outcomes"] else "nothing_to_save",
            "skills": skills, "candidates": proposals, "summary": "Cross-session reflection completed."}
