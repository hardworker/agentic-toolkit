#!/usr/bin/env python3
"""Install or remove owned native hooks without replacing existing hooks."""
from __future__ import annotations

import argparse
import copy
import json
import os
import shlex
import shutil
import sys
from pathlib import Path

from learning import HERE, Store, atomic_text, digest, state_dir


def hook_config(host, root):
    base = [sys.executable, str(root / "runtime" / "learning.py"), "--state-dir", str(root),
            "hook", "--host", host, "--event"]
    result = {}
    for name, event in (("SessionStart", "context"), ("UserPromptSubmit", "context"),
                        ("Stop", "capture"), ("SessionEnd", "capture")):
        handler = {"type": "command", "command": shlex.join(base + [event]), "timeout": 3}
        if host == "codex" and event == "context":
            handler["additionalContextLimit"] = 14000
        result[name] = [{"hooks": [handler]}]
    return result


def merge_hooks(document, owned, remove=False):
    document = copy.deepcopy(document)
    hooks = document.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        raise ValueError("existing hooks must be an object")
    for event, entries in owned.items():
        current = hooks.get(event, [])
        if not isinstance(current, list):
            raise ValueError("existing hook event must be a list")
        # Remove only exact owned handlers, even if someone grouped them with other hooks.
        handlers = [handler for entry in entries for handler in entry["hooks"]]
        retained = []
        for group in current:
            if not isinstance(group, dict) or not isinstance(group.get("hooks"), list):
                retained.append(group)
                continue
            rest = [h for h in group["hooks"] if h not in handlers]
            if rest:
                retained.append(dict(group, hooks=rest))
        if not remove:
            retained += entries
        if retained:
            hooks[event] = retained
        else:
            hooks.pop(event, None)
    return document


def install(home, root, *, remove=False, dry_run=False):
    home, root = Path(home).expanduser().absolute(), Path(root).expanduser().absolute()
    manifest_path = root / "installation.json"
    old = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    updates, links = [], []
    targets = {
        "claude": home / ".claude" / "settings.json",
        "codex": home / ".codex" / "hooks.json",
    }
    for host, path in targets.items():
        if path.is_symlink():
            raise ValueError("preserving symlinked hook config: " + str(path))
        previous = path.read_text() if path.exists() else None
        document = json.loads(previous) if previous else {}
        if not isinstance(document, dict):
            raise ValueError("existing hook config must be an object")
        owned = hook_config(host, root)
        prior = old.get("hooks", {}).get(host)
        if prior:
            document = merge_hooks(document, prior, remove=True)
        document = merge_hooks(document, owned, remove=remove)
        updates.append((path, previous, json.dumps(document, indent=2) + "\n"))
    for host_root in (home / ".claude", home / ".agents"):
        path = host_root / "skills" / "self-learning"
        if path.exists() or path.is_symlink():
            if not path.is_symlink() or path.resolve() != HERE:
                raise ValueError("preserving existing skill: " + str(path))
        links.append(path)
    if dry_run:
        return {"configs": [str(p) for p, _, _ in updates],
                "skills": [str(p) for p in links], "state_dir": str(root)}
    store = Store(root)
    if not remove:
        for name in ("learning.py", "reflection.py", "evidence.py", "upstream_queue.py",
                     "reflection-prompt.md", "UPSTREAM_LICENSE", "LICENSE"):
            atomic_text(root / "runtime" / name, (HERE / name).read_text())
    for host in ("claude", "codex"):
        if not store.config[host + "_bin"]:
            store.config[host + "_bin"] = shutil.which(host)
    for path, previous, updated in updates:
        if previous is not None:
            atomic_text(root / "backups" / (digest(str(path) + previous) + ".json"), previous)
        atomic_text(path, updated)
    for path in links:
        if remove:
            if path.is_symlink():
                path.unlink()
        elif not path.is_symlink():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.symlink_to(HERE, target_is_directory=True)
    store.config["enabled"] = not remove
    atomic_text(root / "config.json", json.dumps(store.config, indent=2) + "\n")
    if remove:
        manifest_path.unlink(missing_ok=True)
    else:
        atomic_text(manifest_path, json.dumps({
            "hooks": {host: hook_config(host, root) for host in targets},
            "home": str(home), "source": str(HERE),
        }, indent=2) + "\n")
    return {"installed": not remove, "state_dir": str(root)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--home", type=Path, default=Path.home())
    parser.add_argument("--state-dir", type=Path)
    parser.add_argument("--uninstall", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    root = args.state_dir or (
        state_dir() if args.home == Path.home() else args.home / ".local/share/agentic-learning")
    os.umask(0o077)
    print(json.dumps(install(args.home, root, remove=args.uninstall, dry_run=args.dry_run), indent=2))


if __name__ == "__main__":
    main()
