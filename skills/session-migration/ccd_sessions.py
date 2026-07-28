#!/usr/bin/env python3
"""Inspect and migrate Claude Code Desktop sessions between accounts, and surface
them in the CLI `claude agents` view."""

import argparse
import datetime
import difflib
import glob
import json
import os
import re
import shutil
import subprocess
import sys

STORE = os.environ.get(
    "CCD_SESSION_STORE",
    os.path.expanduser("~/Library/Application Support/Claude/claude-code-sessions"),
)
APP_CONFIG = os.path.expanduser("~/Library/Application Support/Claude/config.json")
PROJECTS = os.path.expanduser("~/.claude/projects")
JOBS = os.path.expanduser("~/.claude/jobs")

UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I)
SCAN_LINE_CAP = 400

FIELD_WEIGHTS = (
    ("title", 1.00),
    ("worktreeName", 0.90),
    ("branch", 0.85),
    ("cwdBase", 0.80),
    ("firstMessage", 0.70),
    ("cwd", 0.60),
)


def die(msg, code=1):
    print("error: " + msg, file=sys.stderr)
    sys.exit(code)


def iso(ms):
    if not ms:
        return None
    return (
        datetime.datetime.fromtimestamp(ms / 1000, datetime.timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )


def slugify(path):
    return re.sub(r"[/._]", "-", path or "")


def transcript_path(rec):
    cli = rec.get("cliSessionId") or ""
    if not cli:
        return None
    direct = os.path.join(PROJECTS, slugify(rec.get("cwd") or ""), cli + ".jsonl")
    if os.path.exists(direct):
        return direct
    hits = glob.glob(os.path.join(PROJECTS, "*", cli + ".jsonl"))
    return hits[0] if hits else None


def text_of(entry):
    content = (entry.get("message") or {}).get("content")
    if isinstance(content, list):
        content = " ".join(
            b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text"
        )
    return content if isinstance(content, str) else ""


def scan_transcript(rec):
    """First real user message, last assistant message, summed output tokens."""
    path = transcript_path(rec)
    result = {"intent": "", "last": "", "tokens": 0, "path": path, "size": 0}
    if not path:
        return result
    result["size"] = os.path.getsize(path)
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                try:
                    entry = json.loads(line)
                except ValueError:
                    continue
                kind = entry.get("type")
                if kind == "user" and not result["intent"]:
                    body = " ".join(text_of(entry).split())
                    if body and not body.startswith("<") and not body.startswith("Caveman"):
                        result["intent"] = body[:600]
                elif kind == "assistant":
                    body = " ".join(text_of(entry).split())
                    if body:
                        result["last"] = body
                    usage = (entry.get("message") or {}).get("usage") or {}
                    result["tokens"] += usage.get("output_tokens") or 0
    except OSError:
        pass
    return result


def first_user_message(rec):
    return scan_transcript(rec)["intent"][:200]


def transcript_contains(rec, needle):
    path = transcript_path(rec)
    if not path:
        return False
    needle = needle.lower()
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                if needle in line.lower():
                    return True
    except OSError:
        return False
    return False


def parse_ts(value):
    if not isinstance(value, str):
        return 0
    try:
        return int(
            datetime.datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp() * 1000
        )
    except ValueError:
        return 0


def scan_cli_transcripts():
    """Every CLI transcript on disk, keyed by cliSessionId. Header-only read."""
    out = {}
    for path in glob.glob(os.path.join(PROJECTS, "*", "*.jsonl")):
        cli = os.path.basename(path)[:-6]
        if not UUID_RE.match(cli):
            continue
        try:
            st = os.stat(path)
        except OSError:
            continue
        meta = {
            "transcript": path,
            "cwd": "",
            "branch": "",
            "aiTitle": "",
            "createdAt": 0,
            "lastActivityAt": int(st.st_mtime * 1000),
        }
        try:
            with open(path, encoding="utf-8", errors="replace") as fh:
                for i, line in enumerate(fh):
                    if i > SCAN_LINE_CAP or (meta["aiTitle"] and meta["cwd"]):
                        break
                    if '"ai-title"' not in line and '"cwd"' not in line and '"timestamp"' not in line:
                        continue
                    try:
                        entry = json.loads(line)
                    except ValueError:
                        continue
                    if not meta["aiTitle"] and entry.get("type") == "ai-title":
                        meta["aiTitle"] = entry.get("aiTitle") or ""
                    if not meta["cwd"] and entry.get("cwd"):
                        meta["cwd"] = entry["cwd"]
                        meta["branch"] = entry.get("gitBranch") or ""
                    if not meta["createdAt"]:
                        meta["createdAt"] = parse_ts(entry.get("timestamp"))
        except OSError:
            continue
        out[cli] = meta
    return out


def cli_record(cli, meta):
    cwd = meta["cwd"]
    return {
        "path": "",
        "account": "",
        "org": "",
        "sessionId": "",
        "cliSessionId": cli,
        "title": meta["aiTitle"],
        "cwd": cwd,
        "cwdBase": os.path.basename(cwd),
        "originCwd": cwd,
        "worktreePath": "",
        "worktreeName": "",
        "branch": meta["branch"],
        "model": "",
        "bridgeSessionIds": [],
        "spawnSeed": {},
        "isArchived": False,
        "lastActivityAt": meta["lastActivityAt"],
        "createdAt": meta["createdAt"] or meta["lastActivityAt"],
        "hasJob": os.path.isdir(os.path.join(JOBS, cli[:8])),
        "source": "cli",
    }


def accounts():
    if not os.path.isdir(STORE):
        die("session store not found: " + STORE)
    return sorted(d for d in os.listdir(STORE) if os.path.isdir(os.path.join(STORE, d)))


def load_sessions(include_archived=True, include_cli=True):
    out = []
    seen = set()
    for account in accounts():
        for path in glob.glob(os.path.join(STORE, account, "*", "local_*.json")):
            try:
                with open(path, encoding="utf-8") as fh:
                    data = json.load(fh)
            except (OSError, ValueError):
                continue
            if data.get("isArchived") and not include_archived:
                continue
            cwd = data.get("cwd") or ""
            cli = data.get("cliSessionId") or ""
            out.append(
                {
                    "path": path,
                    "account": account,
                    "org": os.path.basename(os.path.dirname(path)),
                    "sessionId": data.get("sessionId") or os.path.basename(path)[:-5],
                    "cliSessionId": cli,
                    "title": data.get("title") or "",
                    "cwd": cwd,
                    "cwdBase": os.path.basename(cwd),
                    "originCwd": data.get("originCwd") or cwd,
                    "worktreePath": data.get("worktreePath") or "",
                    "worktreeName": data.get("worktreeName") or "",
                    "branch": data.get("branch") or "",
                    "model": data.get("model") or "",
                    "bridgeSessionIds": data.get("bridgeSessionIds") or [],
                    "spawnSeed": data.get("spawnSeed") or {},
                    "isArchived": bool(data.get("isArchived")),
                    "lastActivityAt": data.get("lastActivityAt") or 0,
                    "createdAt": data.get("createdAt") or 0,
                    "hasJob": bool(cli) and os.path.isdir(os.path.join(JOBS, cli[:8])),
                    "source": "desktop",
                }
            )
            if cli:
                seen.add(cli)

    if include_cli:
        for cli, meta in scan_cli_transcripts().items():
            if cli in seen:
                continue
            out.append(cli_record(cli, meta))

    out.sort(key=lambda r: r["lastActivityAt"], reverse=True)
    return out


def current_session_id():
    return os.environ.get("CLAUDE_CODE_HOST_SESSION_ID") or ""


def current_account(sessions=None):
    host = current_session_id()
    if host:
        for rec in sessions if sessions is not None else load_sessions(include_cli=False):
            if rec["sessionId"] == host:
                return rec["account"]
    try:
        with open(APP_CONFIG, encoding="utf-8") as fh:
            uuid = json.load(fh).get("lastKnownAccountUuid")
        if uuid and os.path.isdir(os.path.join(STORE, uuid)):
            return uuid
    except (OSError, ValueError):
        pass
    dirs = accounts()
    if not dirs:
        die("no account directories under " + STORE)
    return max(dirs, key=lambda d: os.path.getmtime(os.path.join(STORE, d)))


def tokens(text):
    return [t for t in re.split(r"[^a-z0-9]+", text.lower()) if t]


def field_score(query, candidate):
    if not candidate:
        return 0.0
    q, c = query.lower().strip(), candidate.lower().strip()
    if not q:
        return 0.0
    best = difflib.SequenceMatcher(None, q, c).ratio()
    if q in c:
        best = max(best, 0.90 + 0.10 * (len(q) / max(len(c), 1)))
    qt, ct = tokens(q), tokens(c)
    if qt:
        cset = set(ct)
        exact = sum(1 for t in qt if t in cset)
        partial = sum(1 for t in qt if t not in cset and any(t in x or x in t for x in ct))
        best = max(best, 0.95 * (exact + 0.5 * partial) / len(qt))
    return min(best, 1.0)


def score_record(query, rec, search_transcripts=False):
    best, matched = 0.0, ""
    for field, weight in FIELD_WEIGHTS:
        value = rec.get(field) or ""
        if field == "firstMessage":
            if rec.get("title"):
                continue
            value = rec.setdefault("firstMessage", first_user_message(rec))
        s = weight * field_score(query, value)
        if s > best:
            best, matched = s, "%s=%s" % (field, value[:70])
    if search_transcripts and best < 0.80 and transcript_contains(rec, query):
        best, matched = max(best, 0.80), "transcript"
    return best, matched


def rank(query, sessions, search_transcripts=False, min_score=0.35, limit=10):
    scored = []
    for rec in sessions:
        s, matched = score_record(query, rec, search_transcripts)
        if s >= min_score:
            item = dict(rec)
            item["score"] = round(s, 3)
            item["matchedOn"] = matched
            scored.append(item)
    scored.sort(key=lambda r: (-r["score"], -r["lastActivityAt"]))
    return scored[:limit]


def resolve(ref, sessions):
    ref_l = ref.lower()
    for rec in sessions:
        if ref_l in (rec["sessionId"].lower(), rec["cliSessionId"].lower()):
            return rec
    for rec in sessions:
        ids = [i.lower() for i in (rec["sessionId"], rec["cliSessionId"]) if i]
        if any(ref_l in i for i in ids):
            return rec
    hits = rank(ref, sessions, limit=5)
    if not hits:
        die("no session matches %r — run `list` to see everything" % ref)
    if len(hits) > 1 and hits[0]["score"] - hits[1]["score"] < 0.12:
        lines = ["ambiguous %r — pass an explicit session id:" % ref]
        for h in hits:
            lines.append(
                "  %.2f  %s  %s"
                % (h["score"], h["sessionId"] or h["cliSessionId"], h["title"] or h["cwdBase"])
            )
        die("\n".join(lines))
    top = hits[0]["cliSessionId"] or hits[0]["sessionId"]
    return next(r for r in sessions if (r["cliSessionId"] or r["sessionId"]) == top)


def fmt(rec, current, show_score=False):
    cli_only = rec["source"] == "cli"
    marks = []
    if cli_only:
        marks.append("cli-only (no desktop record)")
    elif rec["account"] == current:
        marks.append("current-account")
    if rec["sessionId"] and rec["sessionId"] == current_session_id():
        marks.append("THIS-SESSION")
    if rec["isArchived"]:
        marks.append("archived")
    marks.append("cli-job" if rec["hasJob"] else "no-cli-job")
    head = "%.2f  " % rec["score"] if show_score else ""
    label = rec["title"] or rec["worktreeName"] or rec["cwdBase"] or "(untitled)"
    out = "%s%-42s  %s" % (head, label[:42], rec["sessionId"] or rec["cliSessionId"])
    out += "\n      account=%s  cwd=%s" % (rec["account"][:8] or "-", rec["cwd"] or "?")
    if rec["branch"]:
        out += "  branch=" + rec["branch"]
    out += "  [" + ", ".join(marks) + "]"
    if show_score and rec.get("matchedOn"):
        out += "\n      matched: " + rec["matchedOn"]
    return out


def cli_version():
    try:
        out = subprocess.run(
            ["claude", "--version"], capture_output=True, text=True, timeout=20
        ).stdout
        m = re.search(r"\d+\.\d+\.\d+", out)
        if m:
            return m.group(0)
    except (OSError, subprocess.SubprocessError):
        pass
    for p in sorted(glob.glob(os.path.join(JOBS, "*", "state.json")), key=os.path.getmtime, reverse=True):
        try:
            with open(p, encoding="utf-8") as fh:
                v = json.load(fh).get("cliVersion")
            if v:
                return v
        except (OSError, ValueError):
            continue
    return None


def build_job(rec, detail=None):
    scan = scan_transcript(rec)
    cli = rec["cliSessionId"]
    if not cli:
        die("session %s has no cliSessionId — nothing to resume" % rec["sessionId"])
    if not scan["path"]:
        die("no CLI transcript found for %s (expected ~/.claude/projects/…/%s.jsonl)" % (rec["sessionId"], cli))
    summary = detail or scan["last"] or (rec["title"] or "session migrated from another account")
    summary = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", summary)
    summary = re.sub(r"[*`#>]+", "", summary)
    summary = " ".join(summary.split())[:200]
    created = iso(rec["createdAt"]) or iso(rec["lastActivityAt"])
    updated = iso(rec["lastActivityAt"]) or created
    bridge = next((b for b in rec["bridgeSessionIds"] if str(b).startswith("cse_")), None)
    state = {
        "state": "done",
        "detail": summary,
        "tempo": "idle",
        "inFlight": {"tasks": 0, "queued": 0, "kinds": []},
        "tokens": scan["tokens"],
        "output": {"result": summary},
        "children": None,
        "linkScanOffset": scan["size"],
        "linkScanPath": scan["path"],
        "template": "claude",
        "respawnFlags": ["--agent", "claude"],
        "intent": scan["intent"] or (rec["title"] or ""),
        "name": rec["title"] or rec["worktreeName"] or rec["cwdBase"] or cli[:8],
        "nameSource": "auto",
        "sessionId": cli,
        "resumeSessionId": cli,
        "daemonShort": cli[:8],
        "cwd": rec["cwd"],
        "originCwd": rec["originCwd"] or rec["cwd"],
        "providerEnv": {},
        "backend": "daemon",
        "createdAt": created,
        "updatedAt": updated,
        "firstTerminalAt": updated,
    }
    version = cli_version()
    if version:
        state["cliVersion"] = version
    if bridge:
        state["bridgeSessionId"] = bridge
        state["bridgeOutboundOnly"] = False
    if rec["worktreePath"]:
        state["worktreePath"] = rec["worktreePath"]
        if rec["spawnSeed"].get("worktreeHookBased"):
            state["worktreeHookBased"] = True
    timeline = {"at": updated, "state": "done", "detail": summary, "text": ""}
    return state, timeline


def write_job(rec, detail=None, dry_run=False, force=False):
    state, timeline = build_job(rec, detail)
    job_dir = os.path.join(JOBS, state["daemonShort"])
    exists = os.path.isdir(job_dir)
    if exists and not force:
        print("  cli job already exists: %s (use --force to rewrite)" % job_dir)
        return job_dir
    print("  cli job  %s  name=%s" % (job_dir, state["name"]))
    print("           resume=%s  cwd=%s" % (state["resumeSessionId"], state["cwd"]))
    if dry_run:
        return job_dir
    os.makedirs(job_dir, exist_ok=True)
    with open(os.path.join(job_dir, "state.json"), "w", encoding="utf-8") as fh:
        json.dump(state, fh, indent=1)
    with open(os.path.join(job_dir, "timeline.jsonl"), "w", encoding="utf-8") as fh:
        fh.write(json.dumps(timeline) + "\n")
    return job_dir


def cmd_accounts(args):
    sessions = load_sessions()
    current = current_account(sessions)
    for account in accounts():
        mine = [r for r in sessions if r["account"] == account]
        orgs = sorted({r["org"] for r in mine})
        print(
            "%s%s  sessions=%d  cli-jobs=%d  orgs=%s"
            % (
                "* " if account == current else "  ",
                account,
                len(mine),
                sum(1 for r in mine if r["hasJob"]),
                ",".join(o[:8] for o in orgs) or "-",
            )
        )
    cli_only = [r for r in sessions if r["source"] == "cli"]
    print(
        "  (no account)                          transcripts=%d  cli-jobs=%d  CLI-only, never in the desktop app"
        % (len(cli_only), sum(1 for r in cli_only if r["hasJob"]))
    )
    print("\n* = account the desktop app is signed into now")


def cmd_list(args):
    sessions = load_sessions(include_archived=args.include_archived)
    current = current_account(sessions)
    if args.source != "all":
        sessions = [r for r in sessions if r["source"] == args.source]
    if args.account:
        sessions = [r for r in sessions if r["account"].startswith(args.account)]
    elif not args.all:
        sessions = [r for r in sessions if r["account"] != current or r["source"] == "cli"]
    if args.json:
        print(json.dumps(sessions, indent=2))
        return
    if not sessions:
        print("no sessions matched")
        return
    for rec in sessions:
        print(fmt(rec, current))
        print()


def cmd_find(args):
    sessions = load_sessions(include_archived=True)
    current = current_account(sessions)
    hits = rank(
        args.query,
        sessions,
        search_transcripts=args.search_transcripts,
        min_score=args.min_score,
        limit=args.limit,
    )
    if args.json:
        print(json.dumps(hits, indent=2))
        return
    if not hits:
        print("no session scored >= %.2f for %r" % (args.min_score, args.query))
        print("try --search-transcripts or a shorter query")
        return
    for rec in hits:
        print(fmt(rec, current, show_score=True))
        print()


def cmd_import(args):
    sessions = load_sessions(include_archived=True)
    current = current_account(sessions)
    rec = resolve(args.session, sessions)
    cli = rec["cliSessionId"]
    if not cli:
        die("session %s has no cliSessionId — nothing to import" % rec["sessionId"])
    if not transcript_path(rec):
        die("no CLI transcript for %s — import reads the transcript, not the record" % cli)

    imported_id = "local_" + cli
    owned = {imported_id, rec["sessionId"]} - {""}
    clash = [r for r in sessions if r["account"] == current and r["sessionId"] in owned]
    if clash and not args.force:
        die(
            "current account already holds %s — importing would duplicate the conversation "
            "in recents (use --force to import anyway)" % clash[0]["sessionId"]
        )

    print("import  %s" % cli)
    print("  title    %s" % (rec["title"] or "(untitled)"))
    print("  cwd      %s" % rec["cwd"])
    print("  becomes  %s in account %s" % (imported_id, current))
    print("  deeplink claude://resume?session=%s" % cli)
    if args.dry_run:
        print("\ndry run — nothing opened")
        return
    subprocess.run(["open", "claude://resume?session=" + cli], check=True)
    print("\nopened. The app imports it and navigates to it — no restart needed.")
    if rec["title"]:
        print('Now set the title back: set_session_title(%s, "%s")' % (imported_id, rec["title"]))
    print("The imported record carries cwd + transcript only: title, model and")
    print("created/last-activity timestamps are reset to import time.")


def cmd_resume(args):
    sessions = load_sessions(include_archived=True)
    rec = resolve(args.session, sessions)
    cli = rec["cliSessionId"]
    if not cli:
        die("session %s has no cliSessionId — nothing for the CLI to resume" % rec["sessionId"])
    path = transcript_path(rec)
    if not path:
        die("no transcript on disk for %s — the CLI has nothing to resume" % cli)

    print("resume  %s" % (rec["title"] or "(untitled)"))
    print("  source     %s" % rec["source"])
    print("  transcript %s" % path)
    print("  cli job    %s" % ("yes" if rec["hasJob"] else "no — run `job` to list it in `claude agents`"))
    print("\n  cd %s && claude --resume %s" % (rec["cwd"] or ".", cli))
    print("  (add --fork-session to branch off instead of continuing in place)")


def cmd_job(args):
    sessions = load_sessions(include_archived=True)
    rec = resolve(args.session, sessions)
    print(
        "cli job entry for %s (%s)"
        % (rec["sessionId"] or rec["cliSessionId"], rec["title"] or "untitled")
    )
    write_job(rec, detail=args.detail, dry_run=args.dry_run, force=args.force)
    if args.dry_run:
        print("\ndry run — nothing written")
    else:
        print("\ndone. Quit and reopen `claude agents` — the list is read at startup.")


def cmd_move(args):
    sessions = load_sessions(include_archived=True)
    current = current_account(sessions)
    rec = resolve(args.session, sessions)
    if rec["source"] == "cli":
        die(
            "%s is a CLI-only session — there is no desktop record to relocate. "
            "Use `import` to give it one in the current account." % rec["cliSessionId"]
        )
    if rec["sessionId"] == current_session_id():
        die("refusing to move the session that is running right now")
    target = args.to or current
    matches = [a for a in accounts() if a == target or a.startswith(target)]
    if len(matches) != 1:
        die("--to %r matched %d accounts; use a full account uuid" % (target, len(matches)))
    target = matches[0]

    twin = "local_" + rec["cliSessionId"]
    if rec["cliSessionId"] and any(
        r["account"] == target and r["sessionId"] == twin and r["sessionId"] != rec["sessionId"]
        for r in sessions
    ):
        die("account %s already has an imported twin (%s) of this conversation" % (target, twin))

    dest = None
    if rec["account"] == target:
        print("already in account %s — desktop side needs nothing" % target)
    else:
        org_dir = os.path.join(STORE, target, rec["org"])
        if not os.path.isdir(org_dir):
            existing = [d for d in sorted(glob.glob(os.path.join(STORE, target, "*"))) if os.path.isdir(d)]
            org_dir = existing[0] if len(existing) == 1 else org_dir
        dest = os.path.join(org_dir, os.path.basename(rec["path"]))
        tomb = os.path.join(org_dir, "deleted_" + rec["sessionId"][len("local_"):])
        if os.path.exists(dest):
            die("destination already exists: " + dest)
        if os.path.exists(tomb) and not args.force:
            die("target account has a deletion tombstone for this session: %s (use --force)" % tomb)

        verb = "copy" if args.copy else "move"
        print("%s  %s" % (verb, rec["sessionId"]))
        print("  title    %s" % (rec["title"] or "(untitled)"))
        print("  cwd      %s" % rec["cwd"])
        print("  from     %s" % rec["path"])
        print("  to       %s" % dest)
        if not args.dry_run:
            os.makedirs(org_dir, exist_ok=True)
            if os.path.exists(tomb):
                os.remove(tomb)
            if args.copy:
                shutil.copy2(rec["path"], dest)
            else:
                shutil.move(rec["path"], dest)

    if not args.no_job:
        write_job(rec, dry_run=args.dry_run, force=args.force)

    if args.dry_run:
        print("\ndry run — nothing written")
        return
    print("\ndone. Transcript stayed at %s" % (transcript_path(rec) or "(not found)"))
    print("Desktop recents: needs a full app restart — the session map lives in the main")
    print("process and is only rebuilt on launch or on an account switch. For an instant")
    print("appearance instead, use `import` (different tradeoffs — see the skill).")
    print("CLI agents view: quit and reopen `claude agents`.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("accounts", help="list account dirs and session counts")
    p.set_defaults(func=cmd_accounts)

    p = sub.add_parser("list", help="list sessions (default: everything outside this account's sidebar)")
    p.add_argument("--all", action="store_true")
    p.add_argument("--account")
    p.add_argument("--include-archived", action="store_true", default=True)
    p.add_argument("--source", choices=["all", "desktop", "cli"], default="all")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("find", help="fuzzy-match by name across all accounts and CLI transcripts")
    p.add_argument("query")
    p.add_argument("--limit", type=int, default=10)
    p.add_argument("--min-score", type=float, default=0.35)
    p.add_argument("--search-transcripts", action="store_true")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_find)

    p = sub.add_parser("resume", help="print the CLI command that reopens a session")
    p.add_argument("session")
    p.set_defaults(func=cmd_resume)

    p = sub.add_parser("import", help="live-import into the current account via claude://resume")
    p.add_argument("session")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--force", action="store_true", help="import even if it would duplicate")
    p.set_defaults(func=cmd_import)

    p = sub.add_parser("job", help="create only the CLI `claude agents` entry")
    p.add_argument("session")
    p.add_argument("--detail", help="override the one-line summary")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_job)

    p = sub.add_parser("move", help="move a session into another account + add CLI entry")
    p.add_argument("session", help="sessionId, cliSessionId, or a fuzzy title")
    p.add_argument("--to", help="target account uuid (default: current account)")
    p.add_argument("--copy", action="store_true", help="leave the original in place")
    p.add_argument("--no-job", action="store_true", help="skip the CLI agents entry")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--force", action="store_true", help="clear a tombstone / rewrite an existing job")
    p.set_defaults(func=cmd_move)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
