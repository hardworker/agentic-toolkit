---
name: session-migration
description: Find a Claude Code session that belongs to another account and surface it in the account signed in now — in the desktop app's recents and in the CLI `claude agents` view. Session records are stored per-account on disk, so after an account switch earlier sessions vanish from the sidebar, from list_sessions and from search_session_transcripts. Use when (1) the user refers to a past session/dialog/conversation and list_sessions or search_session_transcripts turns up nothing matching — check the other accounts before saying it does not exist; (2) the user explicitly asks to migrate/move a session between accounts, or says a session is missing, disappeared, or is not in recents after an account switch. Matches titles fuzzily, so an approximate, partial, or misspelled name is enough.
argument-hint: "[session name] [--import | --move] [--to <accountId>] [--dry-run]"
---

# Session migration between accounts

macOS only — every path below is a macOS Claude Code Desktop location.

## Three surfaces, three stores

| Surface | Backing store | Account-scoped |
|---|---|---|
| Desktop app sidebar / recents | `~/Library/Application Support/Claude/claude-code-sessions/<accountId>/<orgId>/local_<uuid>.json` | **yes** |
| CLI `claude agents` view | `~/.claude/jobs/<first-8-of-cliSessionId>/{state.json,timeline.jsonl}` | no |
| CLI `claude --resume` | `~/.claude/projects/<slug(cwd)>/<cliSessionId>.jsonl` | no |

- The desktop record is metadata only (`title`, `cwd`, `branch`, `worktreeName`, `model`, `cliSessionId`, …). Account-scoped, which is why an account switch hides sessions.
- The **transcript never moves** — it is already visible to `claude --resume` from any account.
- The app loads every record in the current account/org into an **in-memory map in the main process**, and rebuilds it only on launch or on an account switch. There is no file watcher: a record dropped into the directory is invisible until the app restarts.
- A past *interactive desktop* session has **no job entry**, so it never appears in `claude agents` even under the right account. The entry must be synthesized — independent of migration.
- Deletion in the desktop UI writes a `deleted_<uuid>` tombstone (a file holding the deletion epoch-ms). Migrating into an account that holds a tombstone for the session needs `--force`, which clears it.
- `git-worktrees.json` leases worktrees by host session id and is account-agnostic — no edit needed.

Current account: `$CLAUDE_CODE_HOST_SESSION_ID` names the live session; the account directory holding it is the current one. Fallback is `lastKnownAccountUuid` in `~/Library/Application Support/Claude/config.json`.

## Two ways into the desktop sidebar — pick one, never both

| | `import` (live) | `move` (full fidelity) |
|---|---|---|
| Mechanism | `claude://resume?session=<cliSessionId>` deep link → the app's own CLI-session import | relocates the record file between account directories |
| Appears | immediately, and the app navigates to it | only after a **full app restart** |
| Keeps | transcript, cwd | transcript, cwd, title, branch, worktree, model, permission mode |
| Loses | title, model, and the original created / last-activity timestamps (reset to import time) | nothing |
| New id | `local_<cliSessionId>` — a *new* record; the original stays in the old account | same `local_<uuid>` record, relocated |

Default to **`import`** when the user wants the session back in front of them now, then restore the title with `set_session_title`. Use **`move`** when history fidelity matters more than immediacy, or when the user is fine restarting the app.

Doing both produces two sidebar rows for one conversation. Both subcommands refuse when the other has already run; `--force` overrides.

## Tool

`ccd_sessions.py`, in this skill's directory (the same directory as this SKILL.md). Everything below is `python3 <skill-dir>/ccd_sessions.py <subcommand>`; start with:

```bash
python3 <skill-dir>/ccd_sessions.py accounts
```

| Command | Purpose |
|---|---|
| `accounts` | Account dirs, session counts, CLI-job counts, which account is signed in (`*`) |
| `list [--all] [--account ID] [--json]` | Sessions; default is *other* accounts only |
| `find QUERY [--search-transcripts] [--limit N] [--min-score F]` | Fuzzy match by name across all accounts |
| `import REF [--force] [--dry-run]` | Live import into the current account via the deep link |
| `move REF [--to ACCOUNT] [--copy] [--no-job] [--force] [--dry-run]` | Relocate the record **and** create the CLI job entry |
| `job REF [--detail TEXT] [--force] [--dry-run]` | CLI job entry only — no account change |

`find` scores title, worktree name, branch, cwd basename, and — for untitled sessions — the first real user message from the transcript. `--search-transcripts` also greps transcript bodies, for when the user remembers content rather than a name. Listings flag `cli-job` / `no-cli-job`.

`REF` is a `sessionId`, a `cliSessionId`, or a fuzzy title. Ambiguous fuzzy input (top two within 0.12) is refused with the candidates printed — pass an explicit id then.

`job` derives `name` from the title, `intent` from the first user message, and `detail`/`output.result` from the last assistant message. That last one is raw transcript text, so **prefer a crafted one-liner** via `--detail "…"` — it is the text shown after `Done ·` in the agents view.

## Procedure

1. **Locate.** `find "<what the user called it>"`. Widen with a shorter query, a lower `--min-score`, or `--search-transcripts` before concluding it is not there. `list --all` is the fallback.
2. **Confirm with the user** which session, by title + cwd + branch. Never guess between plausible candidates.
3. **Pick the path** using the table above; say which one you are using and what it costs.
4. **Preview** with `--dry-run`, then apply.
5. **After `import`**: restore the title — the import leaves it untitled, and the script prints what to set. If your environment exposes session management (`set_session_title`), call it with `local_<cliSessionId>`; otherwise tell the user to rename the session in the app.
6. **CLI view**: `job <REF> --detail "<one-liner>"` if the session should also show in `claude agents`. `move` does this automatically.
7. **Verify before reporting success**: `list_sessions` must show the session for `import`; `claude agents --json --all` must contain the `cliSessionId` for `job`.
8. **Refresh instructions**: `move` needs a full desktop restart; the `claude agents` list is read at startup, so it needs a quit and reopen.

## Rules

- Get explicit confirmation before `import` or a real `move`. `import` navigates the user's desktop window away from whatever they are looking at, and `move` changes which account owns the session. `--dry-run` and `job` need no confirmation.
- Never move the running session; the script blocks it.
- Nothing is deleted: `move` renames, `--copy` duplicates, an existing destination is refused. The only removal is a tombstone under `--force`.
- Do not hand-edit a record to change ownership — the file's location *is* the ownership.
- Do not patch a record the app has loaded; the in-memory copy wins and will overwrite it. Use `set_session_title` for renames.
- Out of scope: `~/Library/Application Support/Claude/local-agent-mode-sessions/` is a separate per-account store for agent-mode sessions.

## When triggered implicitly

If a session search came up empty, run `find` before reporting the session as missing. Report it as *found in another account*, name it, and offer the two paths — do not migrate unprompted.
