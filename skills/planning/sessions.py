#!/usr/bin/env python3
"""Register named planning sessions; stdlib only, no learning dependency."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import unicodedata
from urllib.parse import quote
import uuid

MARKER = "<!-- grounded-plan-session\n"


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def library_root(store=None):
    return Path(store or os.environ.get("GROUNDED_PLAN_HOME") or
                "~/.local/share/grounded-plan").expanduser().resolve()


def project_scope(project):
    path = Path(project).expanduser().resolve()
    try:
        value = subprocess.run(["git", "-C", str(path), "rev-parse", "--path-format=absolute",
                                "--git-common-dir"], check=True, capture_output=True,
                               text=True, timeout=2).stdout.strip()
        return str(Path(value).resolve())
    except (OSError, subprocess.SubprocessError):
        return str(path)


def slug(title):
    value = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", value).strip("-")[:64].rstrip("-") or "session"


def atomic(path, content):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name("." + uuid.uuid4().hex)
    try:
        with temporary.open("x", encoding="utf-8") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def entry(path):
    text = Path(path).read_text()
    if not text.startswith(MARKER):
        raise ValueError("not a managed session entry: " + str(path))
    data = json.loads(text[len(MARKER):text.index("\n-->")])
    if data.get("version") != 1:
        raise ValueError("unsupported session entry version")
    data["entry"] = str(Path(path).resolve())
    return data


def all_entries(root):
    folder = root / "sessions"
    if folder.is_symlink():
        raise ValueError("managed sessions directory must not be a symlink")
    paths = sorted(folder.glob("*/README.md"))
    if any(p.is_symlink() or p.parent.is_symlink() for p in paths):
        raise ValueError("managed session entries must not be symlinks")
    return [entry(p) for p in paths]


def resolve(root, project, session=None, sources=()):
    scope = project_scope(project)
    entries = all_entries(root)
    if session:
        matches = [e for e in entries if e["id"] == session or
                   Path(session).expanduser().resolve() in
                   (Path(e["entry"]), Path(e["entry"]).parent)]
    else:
        matches = [e for e in entries if e["scope"] == scope and
                   set(sources) & {s["id"] for s in e["sources"]}]
    if len(matches) != 1:
        raise ValueError("session match is absent or ambiguous; select an explicit ID/path or create new work")
    if matches[0]["scope"] != scope:
        raise ValueError("session belongs to another project")
    return matches[0]


def markdown_link(title, path, folder):
    destination = os.path.relpath(path, folder)
    label = str(title).replace("[", "\\[").replace("]", "\\]").replace("\n", " ")
    return "[" + label + "](" + quote(destination, safe="/.:~-") + ")"


def render(data):
    folder = Path(data["entry"]).parent
    metadata = {k: v for k, v in data.items() if k != "entry"}
    text = MARKER + json.dumps(metadata, indent=2, ensure_ascii=False).replace("-->", "--\\u003e")
    text += "\n-->\n\n# " + data["title"] + "\n\n"
    text += "Session: `" + data["id"] + "` · Project: " + data["project"] + "\n\n"
    text += "Reference: " + data["reference"] + "\n\n"
    text += data["summary"] + "\n\nNext: " + data["next"] + "\n"
    for kind in ("plan", "evidence", "artifact", "outcome"):
        links = [link for link in data["links"] if link["kind"] == kind]
        if links:
            text += "\n## " + kind.title() + "s\n\n"
            for link in links:
                exists = Path(link["path"]).is_file()
                text += "- " + markdown_link(link["title"], link["path"], folder)
                text += " — `" + link["id"] + "` · owner: " + link["owner"]
                if not exists:
                    text += " · unavailable"
                text += "\n"
    listing = data.get("learning")
    if listing:
        text += "\n## Related learning\n\nLast refreshed: " + listing["refreshed"]
        text += " · " + ("available" if listing["available"] else "unavailable") + "\n\n"
        for item in listing["artifacts"]:
            text += "- " + markdown_link(item["title"], item["path"], folder)
            text += " — `" + item["id"] + "` · owner: self-learning · revision "
            text += str(item["revision"]) + " · " + item["status"]
            if not item["available"]:
                text += " · unavailable"
            text += "\n"
            for relation in item["relationships"]:
                text += "  - " + relation["kind"] + ": " + ", ".join(relation["sessions"]) + "\n"
            for outcome in item["reported_outcomes"]:
                text += "  - Reported " + outcome["verdict"] + ": " + outcome["note"].replace("\n", " ")
                text += " (evidence: `" + outcome["evidence_id"] + "`; source: "
                source = outcome["session"] or ("unattributed manual feedback"
                         if outcome["evidence_id"].startswith("user-") else "source unavailable")
                text += source + ")\n"
    return text


def index(root):
    lines = ["# Planning library", "", "Derived navigation; session entries and plans are authoritative.", ""]
    for data in all_entries(root):
        lines.append("- " + markdown_link(data["title"], data["entry"], root) +
                     " — `" + data["id"] + "` · " + data["project"] + " · updated " + data["updated"] + " · " + data["summary"].replace("\n", " "))
    legacy = sorted((root / "records").glob("*.md"))
    if legacy:
        lines += ["", "## Legacy records", ""]
        for path in legacy:
            text = path.read_text()
            title = next((line[2:] for line in text.splitlines() if line.startswith("# ")), path.stem)
            lines.append("- " + markdown_link(title, path, root) + " — `" + record_id(path) + "`")
    atomic(root / "index.md", "\n".join(lines) + "\n")


def record_id(path):
    match = re.search(r"^ID:\s*(\S+)", Path(path).read_text(), re.M)
    return match[1] if match else Path(path).stem


def plan_locations(root, identifier):
    paths = {p.resolve() for p in (root / "records").glob("*.md") if record_id(p) == identifier}
    for data in all_entries(root):
        paths.update(Path(link["path"]) for link in data["links"]
                     if link["kind"] == "plan" and link["id"] == identifier)
    return sorted(str(path) for path in paths)


def save(root, data):
    data["updated"] = now()
    atomic(data["entry"], render(data))
    try:
        index(root)
        return dict(data, indexed=True)
    except (OSError, ValueError) as exc:
        return dict(data, indexed=False, index_error=str(exc))


@contextmanager
def locked(root):
    root.mkdir(parents=True, exist_ok=True)
    lock_path = root / ".sessions.lock"
    if lock_path.is_symlink():
        raise ValueError("session lock must not be a symlink")
    with lock_path.open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        yield


def create(root, project, title, key, sources=()):
    scope = project_scope(project)
    existing = [e for e in all_entries(root) if e["scope"] == scope and e["key"] == key]
    if existing:
        return existing[0]
    folder = root / "sessions" / slug(title)
    while folder.exists():
        folder = root / "sessions" / (slug(title) + "-" + uuid.uuid4().hex[:8])
    return {"version": 1, "id": "session-" + uuid.uuid4().hex, "key": key,
            "title": title, "project": Path(project).expanduser().resolve().name,
            "scope": scope, "reference": scope, "sources": [{"id": s, "title": ""} for s in sources],
            "created": now(), "updated": now(), "entry": str(folder / "README.md"),
            "summary": "Planned — outcomes pending.", "next": "Develop the plan.", "links": []}


def attach(data, kind, path, title=None, identifier=None, owner="planning"):
    path = Path(path).expanduser().resolve()
    if owner != "planning" and not identifier:
        raise ValueError("externally owned artifacts require their canonical ID")
    identifier = identifier or (record_id(path) if kind == "plan" and path.is_file() else str(path))
    link = {"kind": kind, "path": str(path), "title": title or path.stem,
            "id": identifier, "owner": owner}
    data["links"] = [old for old in data["links"] if not
                     (old["id"] == identifier and old["owner"] == owner and old["kind"] == kind)] + [link]


def new_plan(root, data, title, content, destination=None, identifier=None):
    folder = Path(data["entry"]).parent
    path = Path(destination).expanduser().resolve() if destination else folder / "plans" / (slug(title) + ".md")
    if not destination:
        if path.parent.is_symlink():
            raise ValueError("implicit plan directory must not be a symlink; select an explicit destination")
        while path.exists():
            path = path.with_name(slug(title) + "-" + uuid.uuid4().hex[:8] + ".md")
    if identifier and plan_locations(root, identifier):
        raise ValueError("plan ID already exists; attach or continue the canonical plan")
    if not identifier:
        while True:
            identifier = datetime.now(timezone.utc).date().isoformat() + "-" + slug(title) + "-" + uuid.uuid4().hex[:6]
            if not plan_locations(root, identifier):
                break
    if re.search(r"^ID:", content, re.M):
        raise ValueError("use attach for an existing plan ID; new plan content must not contain ID metadata")
    path.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation protects explicit destinations outside the library lock.
    with path.open("x", encoding="utf-8") as out:
        out.write("# " + title + "\n\nID: " + identifier + "\nCreated: " + now() + "\n\n" + content)
    attach(data, "plan", path, title, identifier)
    return path


def refresh(data, project, learning_cli, state_dir=None):
    command = [sys.executable, str(Path(learning_cli).expanduser())]
    if state_dir:
        command += ["--state-dir", str(state_dir)]
    command += ["discover", "--project", str(project)]
    for source in data["sources"]:
        command += ["--source", source["id"]]
    # No source association must not accidentally list the entire project.
    if not data["sources"]:
        command += ["--source", "unassociated:"]
    for link in data["links"]:
        if link["owner"] == "self-learning":
            command += ["--artifact", link["id"]]
    try:
        listing = json.loads(subprocess.run(command, check=True, capture_output=True,
                                            text=True, timeout=15).stdout)
        if listing.get("owner") != "self-learning":
            raise ValueError("unexpected discovery owner")
        compact_listing = {key: listing[key] for key in ("available", "refreshed", "database")}
        compact_listing["artifacts"] = []
        for artifact in listing["artifacts"]:
            compact = {key: artifact[key] for key in
                       ("id", "title", "path", "revision", "status", "available", "relationships")}
            compact["reported_outcomes"] = [dict(outcome, note=outcome["note"][:240])
                                             for outcome in artifact["reported_outcomes"][-3:]]
            compact_listing["artifacts"].append(compact)
        data["learning"] = compact_listing
    except (OSError, subprocess.SubprocessError, ValueError, KeyError, TypeError) as exc:
        # Preserve the last known snapshot and every explicitly selected link.
        listing = data.setdefault("learning", {"artifacts": []})
        listing.update(available=False, refreshed=now(), error=str(exc))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store")
    parser.add_argument("--project", default=os.getcwd())
    commands = parser.add_subparsers(dest="command", required=True)
    create_parser = commands.add_parser("create")
    create_parser.add_argument("--title", required=True)
    create_parser.add_argument("--reference", help="stable repository/document/topic reference")
    create_parser.add_argument("--key", required=True, help="stable task key; reuse only for the same work")
    create_parser.add_argument("--source", action="append", default=[])
    for name in ("open", "attach", "plan", "update", "refresh"):
        cmd = commands.add_parser(name)
        cmd.add_argument("--session")
        cmd.add_argument("--source", action="append", default=[])
        if name == "attach":
            cmd.add_argument("--path", required=True)
            cmd.add_argument("--kind", choices=["plan", "evidence", "artifact", "outcome"], required=True)
            cmd.add_argument("--id")
            cmd.add_argument("--owner", default="planning")
            cmd.add_argument("--title")
        elif name == "plan":
            cmd.add_argument("--title", required=True)
            cmd.add_argument("--content-file", type=Path, required=True)
            cmd.add_argument("--destination")
            cmd.add_argument("--id")
        elif name == "update":
            cmd.add_argument("--title")
            cmd.add_argument("--source-title")
            cmd.add_argument("--reference")
            cmd.add_argument("--summary")
            cmd.add_argument("--next")
        elif name == "refresh":
            cmd.add_argument("--learning-cli", required=True)
            cmd.add_argument("--state-dir")
    lookup = commands.add_parser("find")
    lookup.add_argument("--id", required=True)
    commands.add_parser("index")
    args = parser.parse_args()
    for source in getattr(args, "source", []):
        if not re.fullmatch(r"(?:claude|codex):[^\s:]+", source):
            parser.error("source must be a host-qualified native ID (claude:<id> or codex:<id>)")
    root = library_root(args.store)
    if args.command == "find":
        print(json.dumps({"root": str(root), "id": args.id, "paths": plan_locations(root, args.id)}, indent=2))
        return
    with locked(root):
        if args.command == "index":
            index(root)
            print(json.dumps({"root": str(root), "indexed": True}))
            return
        if args.command == "create":
            data = create(root, args.project, args.title, args.key, args.source)
            if args.reference is not None:
                data["reference"] = args.reference
        else:
            data = resolve(root, args.project, args.session, args.source)
        for source in args.source:
            if source not in {s["id"] for s in data["sources"]}:
                data["sources"].append({"id": source, "title": ""})
        if args.command == "attach":
            identifier = args.id or (record_id(args.path) if args.kind == "plan" and
                                    Path(args.path).is_file() else None)
            if args.kind == "plan" and identifier:
                known = plan_locations(root, identifier)
                if any(Path(path) != Path(args.path).expanduser().resolve() for path in known):
                    raise ValueError("plan ID already has a different canonical path")
            attach(data, args.kind, args.path, args.title, identifier, args.owner)
        elif args.command == "plan":
            new_plan(root, data, args.title, args.content_file.read_text(), args.destination, args.id)
        elif args.command == "update":
            for key in ("title", "summary", "next", "reference"):
                if getattr(args, key) is not None:
                    data[key] = getattr(args, key)
            if args.source_title is not None:
                for source in data["sources"]:
                    if source["id"] in args.source:
                        source["title"] = args.source_title
        elif args.command == "refresh":
            refresh(data, args.project, args.learning_cli, args.state_dir)
        result = save(root, data)
        print(json.dumps(dict(result, root=str(root)), indent=2))
        if not result["indexed"]:
            print("Session saved; index needs repair: " + result["index_error"], file=sys.stderr)


if __name__ == "__main__":
    main()
