#!/usr/bin/env python3
"""Shared, event-driven learning for Claude Code and Codex (Python stdlib only)."""
from __future__ import annotations

import argparse
from contextlib import closing
from datetime import datetime, timezone
import fcntl
import json
import os
import re
import sqlite3
import subprocess
import sys
import time
import uuid
from pathlib import Path

from evidence import digest, read_evidence, redact, row_count
from upstream_queue import ReviewQueue

HERE = Path(__file__).resolve().parent
DEFAULTS = {
    "enabled": True, "engine": "auto", "model": None, "auto_skills": True,
    "codex_bin": None, "claude_bin": None,
    "min_interval_seconds": 900, "max_calls_per_day": 6,
    "timeout_seconds": 180, "max_input_chars": 32000, "max_sessions": 12,
}
RECALL_STOPWORDS = set("""
a about again all also an and any are as at be before both but by can change check
compare could describe do does explain find fix for from give had has have help how
i if in inspect investigate is it its just local look make me my need of on or our
outline please procedure procedures project run see should show some task tell than
that the their them then there these they this those to try up use using want was we
were what when where which who why will with without work would you your
""".split())


def state_dir():
    return Path(os.environ.get("AGENTIC_LEARNING_HOME",
                               "~/.local/share/agentic-learning")).expanduser().absolute()


def private_dir(path):
    path = Path(path).absolute()
    for parent in (path, *path.parents):
        if parent.is_symlink():
            raise ValueError("learning directories must not be symlinks")
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    path.chmod(0o700)
    return path


def atomic_text(path, text):
    path = Path(path)
    private_dir(path.parent)
    if path.is_symlink():
        raise ValueError("managed file must not be a symlink")
    tmp = path.parent / ("." + uuid.uuid4().hex)
    try:
        with tmp.open("x", encoding="utf-8") as out:
            tmp.chmod(0o600)
            out.write(text)
            out.flush()
            os.fsync(out.fileno())
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


def project_identity(cwd):
    cwd = Path(cwd).expanduser().resolve()
    try:
        run = subprocess.run(
            ["git", "-C", str(cwd), "rev-parse", "--path-format=absolute", "--git-common-dir"],
            capture_output=True, text=True, timeout=2, check=True)
        identity = str(Path(run.stdout.strip()).resolve())
    except (OSError, subprocess.SubprocessError):
        identity = str(cwd)
    return digest(identity), str(cwd)


def artifact_path(root, row):
    folder = Path(root) / ("skills" if row["kind"] == "skill" else "proposals") / row["project"]
    return folder / row["slug"] / "SKILL.md" if row["kind"] == "skill" else folder / (row["slug"] + ".md")


def discover(root, project, sources=(), selected=()):
    """Read a snapshot without Store initialization, schema changes or receipts."""
    root = Path(root).expanduser().absolute()
    database = root / "learning.sqlite3"
    result = {"available": database.is_file(), "owner": "self-learning",
              "project": project, "database": str(database),
              "refreshed": datetime.now(timezone.utc).isoformat(timespec="seconds"),
              "artifacts": []}
    if not result["available"]:
        return result
    sources, selected = set(sources), set(selected)
    with closing(sqlite3.connect(database.as_uri() + "?mode=ro", uri=True)) as db:
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA query_only=ON")
        # A transaction keeps relationships and revisions in the same snapshot.
        db.execute("BEGIN")
        for row in db.execute("SELECT * FROM artifacts WHERE project=? ORDER BY id", (project,)):
            evidence = []
            references = [(row["revision"], ref) for ref in json.loads(row["evidence_json"])]
            for revision in db.execute("SELECT revision,value FROM revisions WHERE artifact=?",
                                       (row["id"],)):
                references.extend((revision["revision"], ref)
                                  for ref in json.loads(revision["value"])["evidence"])
            seen = set()
            for revision, ref in references:
                identity = (revision, ref["id"], ref["quote"])
                if identity in seen:
                    continue
                seen.add(identity)
                source = db.execute(
                    "SELECT e.id,e.session,e.row_number,s.transcript FROM evidence e "
                    "LEFT JOIN sessions s ON s.id=e.session WHERE e.id=? AND e.project=?",
                    (ref["id"], project)).fetchone()
                evidence.append(dict(source, quote=ref["quote"], revision=revision,
                                     available=bool(source["transcript"] and Path(source["transcript"]).is_file()))
                                if source else dict(ref, revision=revision, session=None,
                                                    transcript=None, available=False))
            deliveries = [dict(r) for r in db.execute(
                "SELECT revision,session,cutoff,created FROM deliveries WHERE artifact=? "
                "ORDER BY created", (row["id"],))]
            outcomes = [dict(r) for r in db.execute(
                "SELECT o.verdict,o.note,o.evidence_id,o.created,e.session,e.row_number,s.transcript "
                "FROM outcomes o LEFT JOIN evidence e ON e.id=o.evidence_id AND e.project=? "
                "LEFT JOIN sessions s ON s.id=e.session WHERE o.artifact=? ORDER BY o.created",
                (project, row["id"]))]
            relationships = []
            for kind, refs in (("supporting-evidence", evidence), ("delivery", deliveries),
                               ("reported-outcome", outcomes)):
                matched = sorted({r["session"] for r in refs if r.get("session") and
                                  (not sources or r["session"] in sources)})
                if matched:
                    relationships.append({"kind": kind, "sessions": matched})
            if sources and not relationships and row["id"] not in selected:
                continue
            path = artifact_path(root, row)
            result["artifacts"].append({
                **{k: row[k] for k in ("id", "kind", "title", "revision", "status", "updated")},
                "owner": "self-learning", "path": str(path), "available": path.is_file(),
                "selected": row["id"] in selected, "relationships": relationships,
                "evidence": evidence, "deliveries": deliveries, "reported_outcomes": outcomes})
    return result


class Store:
    def __init__(self, root):
        self.root = private_dir(root)
        self.queue = ReviewQueue(self.root / "learning.sqlite3")
        self.config = dict(DEFAULTS)
        config_path = self.root / "config.json"
        if config_path.is_symlink():
            raise ValueError("config must not be a symlink")
        if config_path.exists():
            settings = json.loads(config_path.read_text())
            if not isinstance(settings, dict) or set(settings) - set(DEFAULTS):
                raise ValueError("invalid learning config keys")
            self.config.update(settings)
        for key in ("min_interval_seconds", "max_calls_per_day", "timeout_seconds",
                    "max_input_chars", "max_sessions"):
            if type(self.config[key]) is not int or self.config[key] < 1:
                raise ValueError("invalid positive integer setting: " + key)
        for key in ("enabled", "auto_skills"):
            if type(self.config[key]) is not bool:
                raise ValueError("invalid boolean setting: " + key)
        if self.config["engine"] not in {"auto", "claude", "codex"}:
            raise ValueError("engine must be auto, claude or codex")
        if self.config["model"] is not None and not isinstance(self.config["model"], str):
            raise ValueError("model must be a string or null")
        for key in ("codex_bin", "claude_bin"):
            if self.config[key] is not None and (
                    not isinstance(self.config[key], str) or not Path(self.config[key]).is_absolute()):
                raise ValueError("CLI executable paths must be absolute")
        with self.db() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY, project TEXT NOT NULL, cwd TEXT NOT NULL,
                    host TEXT NOT NULL, transcript TEXT NOT NULL, updated REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS evidence (
                    id TEXT PRIMARY KEY, session TEXT NOT NULL, project TEXT NOT NULL,
                    row_number INTEGER NOT NULL, role TEXT NOT NULL, text TEXT NOT NULL,
                    created REAL NOT NULL);
                CREATE INDEX IF NOT EXISTS evidence_scope ON evidence(project, created);
                CREATE TABLE IF NOT EXISTS artifacts (
                    id TEXT PRIMARY KEY, project TEXT NOT NULL, kind TEXT NOT NULL,
                    slug TEXT NOT NULL, title TEXT NOT NULL, description TEXT NOT NULL,
                    body TEXT NOT NULL, evidence_json TEXT NOT NULL,
                    revision INTEGER NOT NULL, status TEXT NOT NULL,
                    notified_revision INTEGER NOT NULL DEFAULT 0, updated REAL NOT NULL);
                CREATE VIRTUAL TABLE IF NOT EXISTS artifact_search USING fts5(
                    id UNINDEXED, project UNINDEXED, title, description, body);
                CREATE TABLE IF NOT EXISTS revisions (
                    artifact TEXT NOT NULL, revision INTEGER NOT NULL,
                    value TEXT NOT NULL, created REAL NOT NULL,
                    PRIMARY KEY(artifact, revision));
                CREATE TABLE IF NOT EXISTS deliveries (
                    artifact TEXT NOT NULL, revision INTEGER NOT NULL, session TEXT NOT NULL,
                    cutoff INTEGER NOT NULL, created REAL NOT NULL,
                    PRIMARY KEY(artifact, revision, session));
                CREATE TABLE IF NOT EXISTS outcomes (
                    artifact TEXT NOT NULL, verdict TEXT NOT NULL, note TEXT NOT NULL,
                    evidence_id TEXT NOT NULL, created REAL NOT NULL,
                    UNIQUE(artifact, evidence_id));
                CREATE TABLE IF NOT EXISTS runs (
                    id INTEGER PRIMARY KEY, project TEXT NOT NULL, started REAL NOT NULL,
                    status TEXT NOT NULL, detail TEXT NOT NULL DEFAULT '');
                CREATE TABLE IF NOT EXISTS notices (id TEXT PRIMARY KEY);
            """)

    def db(self):
        return self.queue._connect()

    def enqueue(self, host, payload):
        lock_path = self.root / "capture.lock"
        if lock_path.is_symlink():
            raise ValueError("capture lock must not be a symlink")
        with lock_path.open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            return self._enqueue(host, payload)

    def _enqueue(self, host, payload):
        transcript = Path(payload["transcript_path"]).expanduser().absolute()
        cutoff = row_count(transcript)
        session = host + ":" + str(payload["session_id"])
        project, cwd = project_identity(payload["cwd"])
        with self.db() as db:
            old = db.execute("SELECT project FROM sessions WHERE id=?", (session,)).fetchone()
            if old and old["project"] != project:
                raise ValueError("session changed project")
            db.execute("INSERT OR REPLACE INTO sessions VALUES(?,?,?,?,?,?)",
                       (session, project, cwd, host, str(transcript), time.time()))
        return self.queue.enqueue(
            session_id=session, turn_id=str(cutoff), transcript_path=str(transcript),
            transcript_rows=cutoff, signal=False, signal_source=host,
            trigger="interval", model=host)

    def collect(self, job):
        with self.db() as db:
            session = db.execute("SELECT * FROM sessions WHERE id=?", (job["session_id"],)).fetchone()
        if session is None:
            raise ValueError("job has no source session")
        observations = read_evidence(job["transcript_path"], job["transcript_rows"],
                                     session["host"], job["session_id"])
        with self.db() as db:
            for ev in observations:
                db.execute("INSERT OR IGNORE INTO evidence VALUES(?,?,?,?,?,?,?)",
                           (ev["id"], ev["session"], session["project"], ev["row"],
                            ev["role"], ev["text"], time.time()))
        return dict(session)

    def bundle(self, project):
        with self.db() as db:
            sessions = db.execute(
                "SELECT id FROM sessions WHERE project=? ORDER BY updated DESC LIMIT ?",
                (project, self.config["max_sessions"])).fetchall()
            ids = [r["id"] for r in sessions]
            rows = db.execute(
                "SELECT * FROM evidence WHERE project=? ORDER BY created DESC LIMIT 500",
                (project,)).fetchall()
            available = [dict(r) for r in db.execute(
                "SELECT id,kind,slug,title,description,body,status FROM artifacts "
                "WHERE project=? ORDER BY updated DESC LIMIT 30", (project,))]
            for artifact in available:
                artifact["reported_outcomes"] = [dict(r) for r in db.execute(
                    "SELECT verdict,note,evidence_id FROM outcomes WHERE artifact=? "
                    "ORDER BY created DESC LIMIT 3", (artifact["id"],))]
        artifacts, artifact_size = [], 0
        for item in available:
            item["body"] = item["body"][:1000]
            cost = len(json.dumps(item))
            if artifact_size + cost <= self.config["max_input_chars"] // 3:
                artifacts.append(item)
                artifact_size += cost
        # Prioritize requests before recent results so long traces retain their intent.
        groups = {}
        for session in ids:
            group = [dict(r) for r in rows if r["session"] == session]
            groups[session] = sorted(group, key=lambda r: r["role"] != "user")
        selected, size = [], len(json.dumps(artifacts))
        for index in range(max((len(g) for g in groups.values()), default=0)):
            for group in groups.values():
                if index >= len(group):
                    continue
                ev = group[index]
                cost = len(json.dumps(ev))
                if size + cost <= self.config["max_input_chars"]:
                    selected.append(ev)
                    size += cost
        return {"project": project, "evidence": selected, "artifacts": artifacts}

    def reserve_run(self, project):
        now = time.time()
        with self.db() as db:
            db.execute("BEGIN IMMEDIATE")
            count = db.execute("SELECT COUNT(*) FROM runs WHERE started>?", (now-86400,)).fetchone()[0]
            latest = db.execute("SELECT MAX(started) FROM runs WHERE project=?", (project,)).fetchone()[0]
            if count >= self.config["max_calls_per_day"] or (
                    latest and now-latest < self.config["min_interval_seconds"]):
                db.commit()
                return None
            cursor = db.execute("INSERT INTO runs(project,started,status) VALUES(?,?,'running')",
                                (project, now))
            db.commit()
            return cursor.lastrowid

    def publish(self, project, kind, item):
        identifier = project + ":" + kind + ":" + item["slug"]
        content = {k: item[k] for k in ("title", "description", "body")}
        with self.db() as db:
            db.execute("BEGIN IMMEDIATE")
            old = db.execute("SELECT * FROM artifacts WHERE id=?", (identifier,)).fetchone()
            if old and old["status"] in {"dismissed", "harmful"}:
                db.commit()
                return identifier
            changed = not old or any(old[k] != v for k, v in content.items())
            revision = (old["revision"] if old else 0) + int(changed)
            status = old["status"] if old else (
                "active" if kind == "skill" and self.config["auto_skills"] else "pending")
            db.execute("INSERT OR REPLACE INTO artifacts VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                       (identifier, project, kind, item["slug"], content["title"],
                        content["description"], content["body"], json.dumps(item["evidence"]),
                        revision, status, old["notified_revision"] if old else 0, time.time()))
            if changed:
                db.execute("INSERT INTO revisions VALUES(?,?,?,?)",
                           (identifier, revision, json.dumps(item), time.time()))
            db.execute("DELETE FROM artifact_search WHERE id=?", (identifier,))
            db.execute("INSERT INTO artifact_search VALUES(?,?,?,?,?)",
                       (identifier, project, content["title"], content["description"], content["body"]))
            db.commit()
        self.materialize(identifier)
        return identifier

    def materialize(self, identifier):
        with self.db() as db:
            row = db.execute("SELECT * FROM artifacts WHERE id=?", (identifier,)).fetchone()
            if row is None:
                return
            evs = json.loads(row["evidence_json"])
            sources = []
            for ev in evs:
                source = db.execute(
                    "SELECT e.*,s.transcript FROM evidence e JOIN sessions s ON s.id=e.session "
                    "WHERE e.id=?", (ev["id"],)).fetchone()
                if source:
                    sources.append("- " + ev["id"] + " — " + source["transcript"] +
                                   ":" + str(source["row_number"]) + "\n  " + ev["quote"])
        filename = self.artifact_path(row)
        header = ("---\nname: " + row["slug"] + "\ndescription: " +
                  json.dumps(row["description"], ensure_ascii=False) + "\n---\n\n"
                  if row["kind"] == "skill" else "")
        text = (header + "# " + row["title"] + "\n\n" + row["body"] +
                "\n\nStatus: " + row["status"] + " · Revision: " + str(row["revision"]) +
                "\n\nEvidence:\n" + "\n".join(sources) + "\n")
        atomic_text(filename, text)

    def artifact_path(self, row):
        return artifact_path(self.root, row)

    def feedback(self, identifier, verdict, note, evidence_id):
        if verdict not in {"helpful", "harmful"}:
            raise ValueError("invalid outcome")
        with self.db() as db:
            row = db.execute("SELECT * FROM artifacts WHERE id=?", (identifier,)).fetchone()
            if not row:
                raise ValueError("unknown artifact")
            db.execute("INSERT OR IGNORE INTO outcomes VALUES(?,?,?,?,?)",
                       (identifier, verdict, redact(note)[:1000], evidence_id, time.time()))
            if verdict == "harmful":
                db.execute("UPDATE artifacts SET status='harmful' WHERE id=?", (identifier,))
            elif row["kind"] == "proposal" and row["status"] == "pending":
                db.execute("UPDATE artifacts SET status='helpful' WHERE id=?", (identifier,))
        self.materialize(identifier)

    def context(self, project, prompt="", session="", cutoff=0):
        words = [word for word in dict.fromkeys(re.findall(r"[^\W_]{2,}", prompt.lower()))
                 if word not in RECALL_STOPWORDS][:20]
        query = " OR ".join('"' + word + '"' for word in words)
        with self.db() as db:
            if words:
                rows = db.execute(
                    "SELECT a.* FROM artifact_search JOIN artifacts a ON a.id=artifact_search.id "
                    "WHERE artifact_search MATCH ? AND a.project=? AND a.status='active' "
                    "ORDER BY rank LIMIT 2", (query, project)).fetchall()
            else:
                rows = []
            notes = []
            for row in rows:
                notes.append("Learned procedure " + row["id"] + ":\n" + row["body"])
                if session:
                    db.execute("INSERT OR IGNORE INTO deliveries VALUES(?,?,?,?,?)",
                               (row["id"], row["revision"], session, cutoff, time.time()))
            proposal = db.execute(
                "SELECT a.* FROM artifact_search JOIN artifacts a ON a.id=artifact_search.id "
                "WHERE artifact_search MATCH ? AND a.project=? AND a.kind='proposal' "
                "AND a.status='pending' AND a.notified_revision<a.revision ORDER BY rank LIMIT 1",
                (query, project)).fetchone() if words else None
            if proposal:
                notes.append("New workflow improvement proposal " + proposal["id"] + ":\n" +
                             proposal["title"] + "\n" + proposal["body"][:2000] +
                             "\nRead the full proposal and source citations at " +
                             str(self.artifact_path(proposal)) + "." +
                             "\nBriefly bring this evidence-backed suggestion to the user when relevant. "
                             "The proposal does not authorize implementation. Proposed tooling and "
                             "baselines are future work; verify current capabilities before using them.")
                if session:
                    db.execute("UPDATE artifacts SET notified_revision=revision WHERE id=?", (proposal["id"],))
                    db.execute("INSERT OR IGNORE INTO deliveries VALUES(?,?,?,?,?)",
                               (proposal["id"], proposal["revision"], session, cutoff, time.time()))
            failure = db.execute("SELECT id,status,detail FROM runs WHERE project=? "
                                 "ORDER BY id DESC LIMIT 1", (project,)).fetchone()
            if failure and failure["status"] == "failed":
                notice = "run-" + str(failure["id"])
                seen = db.execute("SELECT 1 FROM notices WHERE id=?", (notice,)).fetchone()
                if not seen:
                    notes.append("Automatic learning needs attention: " + failure["detail"])
                    if session:
                        db.execute("INSERT OR IGNORE INTO notices VALUES(?)", (notice,))
        if not notes:
            return ""
        return ("Local project-scoped learning context. These are generated, revisable procedures; "
                "follow current user instructions when they conflict. Delivery is not proof of usefulness. "
                "Explicit later user reports of helpful or harmful use are reviewed automatically after "
                "the turn, subject to the reflection budget. Do not claim a durable update until confirmed.\n\n" +
                "\n\n".join(notes))[:14000]


def launch_worker(store):
    if os.environ.get("AGENTIC_LEARNING_NO_SPAWN") == "1":
        return
    with store.db() as db:
        if not db.execute("SELECT 1 FROM review_jobs WHERE status IN ('pending','running') LIMIT 1").fetchone():
            return
    log = store.root / "worker.log"
    if log.is_symlink():
        raise ValueError("worker log must not be a symlink")
    with log.open("a") as output:
        log.chmod(0o600)
        env = dict(os.environ, AGENTIC_LEARNING_WORKER="1")
        subprocess.Popen(
            [sys.executable, str(HERE / "learning.py"), "--state-dir", str(store.root), "worker"],
            stdin=subprocess.DEVNULL, stdout=output, stderr=output, env=env,
            cwd=str(HERE), start_new_session=True, close_fds=True)


def hook(store, host, event, payload):
    if not store.config["enabled"] or os.environ.get("AGENTIC_LEARNING_WORKER") == "1":
        return
    if event == "capture":
        store.enqueue(host, payload)
    launch_worker(store)
    if event == "context":
        project, _ = project_identity(payload["cwd"])
        session = host + ":" + str(payload["session_id"])
        try:
            cutoff = row_count(payload["transcript_path"]) if payload.get("transcript_path") else 0
        except FileNotFoundError:
            cutoff = 0
        context = store.context(project, str(payload.get("prompt", "")), session, cutoff)
        if context:
            print(json.dumps({"hookSpecificOutput": {
                "hookEventName": payload.get("hook_event_name", "SessionStart"),
                "additionalContext": context}}))


def worker(store):
    import reflection
    owner = uuid.uuid4().hex
    if not store.config["enabled"] or not store.queue.acquire_worker_lease(owner):
        return
    try:
        store.queue.cleanup()
        for _ in range(20):
            job = store.queue.claim_next(owner)
            if job is None:
                break
            run_id = None
            try:
                session = store.collect(job)
                bundle = store.bundle(session["project"])
                user_sessions = {e["session"] for e in bundle["evidence"] if e["role"] == "user"}
                result = {"status": "nothing_to_save", "skills": [], "candidates": [],
                          "summary": "Evidence captured; waiting for independent sessions or budget."}
                if len(user_sessions) >= 2:
                    run_id = store.reserve_run(session["project"])
                if run_id:
                    with reflection.Heartbeat(store.queue, owner, job["id"]) as heartbeat:
                        response = reflection.run_model(store, bundle, session["host"])
                        heartbeat.beat()
                        if heartbeat.lost:
                            raise RuntimeError("reflection lost queue ownership")
                        result = reflection.apply_result(store, bundle, response)
                    with store.db() as db:
                        db.execute("UPDATE runs SET status='done' WHERE id=?", (run_id,))
                store.queue.heartbeat_job(job["id"], owner)
                if not store.queue.complete(job["id"], owner, result):
                    raise RuntimeError("worker lost job ownership")
            except Exception as exc:
                detail = type(exc).__name__ + ": " + redact(str(exc))[:200]
                if run_id:
                    with store.db() as db:
                        db.execute("UPDATE runs SET status='failed',detail=? WHERE id=?", (detail, run_id))
                store.queue.heartbeat_job(job["id"], owner)
                store.queue.fail(job["id"], owner, code="reflection_failed", message=detail)
    finally:
        store.queue.release_worker_lease(owner)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-dir", type=Path, default=state_dir())
    commands = parser.add_subparsers(dest="command", required=True)
    h = commands.add_parser("hook")
    h.add_argument("--host", choices=["claude", "codex"], required=True)
    h.add_argument("--event", choices=["capture", "context"], required=True)
    commands.add_parser("worker")
    commands.add_parser("status")
    commands.add_parser("enable")
    commands.add_parser("disable")
    listing = commands.add_parser("discover")
    listing.add_argument("--project", default=os.getcwd())
    listing.add_argument("--source", action="append", default=[])
    listing.add_argument("--artifact", action="append", default=[])
    c = commands.add_parser("context")
    c.add_argument("--project", default=os.getcwd())
    c.add_argument("--prompt", default="")
    f = commands.add_parser("feedback")
    f.add_argument("artifact")
    f.add_argument("--verdict", choices=["helpful", "harmful"], required=True)
    f.add_argument("--note", required=True)
    d = commands.add_parser("dismiss")
    d.add_argument("artifact")
    args = parser.parse_args()
    try:
        os.umask(0o077)
        if args.command == "discover":
            print(json.dumps(discover(args.state_dir, project_identity(args.project)[0],
                                      args.source, args.artifact), indent=2))
            return
        store = Store(args.state_dir)
        if args.command == "hook":
            hook(store, args.host, args.event, json.load(sys.stdin))
        elif args.command == "worker":
            worker(store)
        elif args.command == "context":
            print(store.context(project_identity(args.project)[0], args.prompt))
        elif args.command == "feedback":
            store.feedback(args.artifact, args.verdict, args.note, "user-" + uuid.uuid4().hex)
        elif args.command in {"enable", "disable"}:
            store.config["enabled"] = args.command == "enable"
            atomic_text(store.root / "config.json", json.dumps(store.config, indent=2) + "\n")
        elif args.command == "dismiss":
            with store.db() as db:
                db.execute("UPDATE artifacts SET status='dismissed' WHERE id=?", (args.artifact,))
            store.materialize(args.artifact)
        else:
            with store.db() as db:
                artifacts = [dict(r) for r in db.execute(
                    "SELECT id,kind,title,status,revision FROM artifacts ORDER BY updated DESC")]
                runs = [dict(r) for r in db.execute("SELECT * FROM runs ORDER BY id DESC LIMIT 5")]
            print(json.dumps({"state_dir": str(store.root), "config": store.config,
                              "queue": store.queue.status(), "artifacts": artifacts,
                              "recent_runs": runs}, indent=2))
    except Exception as exc:
        if args.command != "hook":
            raise
        # Hooks must not prevent the source task from finishing.
        print("self-learning: " + type(exc).__name__, file=sys.stderr)


if __name__ == "__main__":
    main()
