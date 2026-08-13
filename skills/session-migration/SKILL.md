---
name: session-migration
description: Find any past Claude Code session — desktop or terminal, any account — and surface it wherever the user wants it: the desktop app's recents, the CLI `claude agents` view, or a `claude --resume` command. Desktop records are stored per account, and terminal sessions have no desktop record at all, so both are invisible to list_sessions and search_session_transcripts. Use when (1) the user refers to a past session, dialog or conversation and list_sessions or search_session_transcripts turns up nothing matching — sweep the other accounts and the CLI transcripts before saying it does not exist; (2) the user asks to migrate or move a session between accounts, to get a terminal session into the desktop app, or to reopen a desktop session in the CLI; (3) the user says a session is missing, disappeared, or is not in recents after an account switch. Matches titles fuzzily, so an approximate, partial, or misspelled name is enough.
argument-hint: "[session name] [--import | --move | --resume | --job] [--to <accountId>] [--dry-run]"
---

# Session migration

Find a session anywhere Claude Code keeps one, and put it where the user wants it — desktop sidebar, `claude agents`, or a terminal resume.

macOS only — every desktop path below is a macOS Claude Code Desktop location.

## Three surfaces, three stores

| Surface | Backing store | Account-scoped |
|---|---|---|
| Desktop app sidebar / recents | `~/Library/Application Support/Claude/claude-code-sessions/<accountId>/<orgId>/local_<uuid>.json` | **yes** |
| CLI `claude agents` view | `~/.claude/jobs/<first-8-of-cliSessionId>/{state.json,timeline.jsonl}` | no |
| CLI `claude --resume` | `~/.claude/projects/<slug(cwd)>/<cliSessionId>.jsonl` | no |

- The desktop record is metadata only (`title`, `cwd`, `branch`, `worktreeName`, `model`, `cliSessionId`, …). Account-scoped, which is why an account switch hides sessions.
- The **transcript is the durable artifact** — account-agnostic, resumable by `claude --resume <cliSessionId>` no matter which account (or app) created it. Everything else is a pointer to it.
- Sessions therefore come in two flavours: **desktop** (a record plus a transcript) and **cli-only** (a transcript and nothing else — started in a terminal, so the desktop app has never heard of it). `list`/`find` cover both; `--source cli|desktop` narrows.
- The app loads every record in the current account/org into an **in-memory map in the main process**, and rebuilds it only on launch or on an account switch. There is no file watcher: a record dropped into the directory is invisible until the app restarts.
- A past *interactive desktop* session has **no job entry**, so it never appears in `claude agents` even under the right account. The entry must be synthesized — independent of migration.
- Deletion in the desktop UI writes a `deleted_<uuid>` tombstone (a file holding the deletion epoch-ms). Migrating into an account that holds a tombstone for the session needs `--force`, which clears it.
- `git-worktrees.json` leases worktrees by host session id and is account-agnostic — no edit needed.

Current account: `$CLAUDE_CODE_HOST_SESSION_ID` names the live session; the account directory holding it is the current one. Fallback is `lastKnownAccountUuid` in `~/Library/Application Support/Claude/config.json`.

## Which direction

| The user wants | Subcommand | Works on |
|---|---|---|
| it back in the desktop sidebar | `import` or `move` | desktop records in another account, and cli-only sessions |
| to continue it in the terminal | `resume` | anything with a transcript |
| it listed in `claude agents` | `job` | anything with a transcript |

Desktop → CLI needs no migration at all: the transcript is already there, so `resume` just prints the `cd … && claude --resume <cliSessionId>` line. The only genuinely missing piece on that side is the `claude agents` row, which `job` synthesizes.

CLI → desktop is the direction that needs work, and `import` handles it for both a session stranded in another account and one that has never existed outside the terminal.

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

## Blocked by a background agent

Both paths ultimately run `claude --resume <cliSessionId>`, and that refuses while a background agent holds the session:

```
Error: Session <id> is currently running as a background agent (bg).
Use `claude agents` to find and attach to it, or add --fork-session to branch off a copy.
```

The desktop app surfaces this as **"Claude Code crashed"**, and stamps `error` / `errorCategory: process_crashed` on the record it just created. The record is fine; the resume behind it never started.

The claim is a live listener on `/tmp/cc-daemon-<uid>/*/rv/<first-8-of-cliSessionId>.sock`, not anything in the job's `state.json`. So a job whose `state.json` reads `done` / `idle` can still own the session — and because the agents view files it under completed, **it offers no Stop control**. That combination is the trap: nothing looks running, yet every import crashes.

`import` and `resume` preflight this and refuse with the holding pids. `--force` does not override it — the refusal comes from the CLI, not from the script. `job` and `move` refuse too, for a different reason: the job dir is keyed by the same `cli[:8]` as the socket, so it *is* the live daemon's job dir, and writing the synthesized entry would overwrite a running agent's `state.json` with a fabricated `done` / `idle` — manufacturing the very no-Stop-control state described above. Listings mark the session `bg-socket`, socket presence only, since whether it actually blocks depends on a live holder.

To release it: stop the agent in `claude agents` if it appears there, otherwise it is a leftover daemon — `kill -TERM <pids>`, which also ends its child MCP servers. Check `inFlight.tasks` is 0 in `state.json` first; the transcript is on disk either way, so no conversation data rides on the process. Then re-run the import. `claude --resume <id> --fork-session` is the alternative that needs no claim, at the cost of a duplicate transcript under a new id.

## Tool

`ccd_sessions.py`, in this skill's directory (the same directory as this SKILL.md). Everything below is `python3 <skill-dir>/ccd_sessions.py <subcommand>`; start with:

```bash
python3 <skill-dir>/ccd_sessions.py accounts
```

| Command | Purpose |
|---|---|
| `accounts` | Account dirs, session counts, CLI-job counts, cli-only transcript count, which account is signed in (`*`) |
| `list [--all] [--account ID] [--source desktop\|cli] [--json]` | Sessions; default hides the current account's own desktop records |
| `find QUERY [--search-transcripts] [--limit N] [--min-score F]` | Fuzzy match by name across every account **and** every CLI transcript |
| `resume REF` | Print the `cd … && claude --resume …` line for a session |
| `import REF [--force] [--dry-run]` | Live import into the current account via the deep link |
| `move REF [--to ACCOUNT] [--copy] [--no-job] [--force] [--dry-run]` | Relocate the record **and** create the CLI job entry |
| `job REF [--detail TEXT] [--force] [--dry-run]` | CLI job entry only — no account change |

Listings flag a session `bg-socket` when a rendezvous socket for it exists — see the section above.

`find` scores title, worktree name, branch, cwd basename, and — for untitled sessions — the first real user message from the transcript. For cli-only sessions the title is the CLI's own `ai-title` entry, read from the transcript header. `--search-transcripts` also greps transcript bodies, for when the user remembers content rather than a name. Listings flag `cli-only` and `cli-job` / `no-cli-job`.

The CLI sweep reads the first 400 lines of each transcript (~1s for 160 sessions), so `find` sees terminal sessions the desktop app has never known about.

`REF` is a `sessionId`, a `cliSessionId`, or a fuzzy title. Ambiguous fuzzy input (top two within 0.12) is refused with the candidates printed — pass an explicit id then.

`job` derives `name` from the title, `intent` from the first user message, and `detail`/`output.result` from the last assistant message. That last one is raw transcript text, so **prefer a crafted one-liner** via `--detail "…"` — it is the text shown after `Done ·` in the agents view.

## Procedure

1. **Locate.** `find "<what the user called it>"`. Widen with a shorter query, a lower `--min-score`, or `--search-transcripts` before concluding it is not there. `list --all` is the fallback.
2. **Confirm with the user** which session, by title + cwd + branch. Never guess between plausible candidates.
3. **Pick the direction** from the direction table, then — if it is desktop-bound — the path from the tradeoff table; say which one you are using and what it costs.
4. **Preview** with `--dry-run`, then apply. A background-agent refusal here is the trap above, not a bad ref — release the claim and retry rather than reaching for `--force`.
5. **After `import`**: restore the title — the import leaves it untitled, and the script prints what to set. If the same `sessionId` was deleted in the app UI earlier in this app run, the row stays out of the sidebar even though the import succeeded: the tombstone is cleared and the map is repopulated, but the renderer's own list keeps the deletion until a relaunch. `list_sessions` reporting the session while the user cannot see it is exactly that case — tell them to quit and reopen rather than importing again. If your environment exposes session management (`set_session_title`), call it with `local_<cliSessionId>`; otherwise tell the user to rename the session in the app.
6. **CLI view**: `job <REF> --detail "<one-liner>"` if the session should also show in `claude agents`. `move` does this automatically.
7. **Verify before reporting success**: `list_sessions` must show the session for `import`; `claude agents --json --all` must contain the `cliSessionId` for `job`.
8. **Refresh instructions**: `move` needs a full desktop restart; the `claude agents` list is read at startup, so it needs a quit and reopen.

## Rules

- Get explicit confirmation before `import` or a real `move`. `import` navigates the user's desktop window away from whatever they are looking at, and `move` changes which account owns the session. `--dry-run` and `job` need no confirmation.
- Never move the running session; the script blocks it. `move` also refuses cli-only sessions — there is no record to relocate, so `import` is the only way to give one a desktop presence.
- Nothing is deleted: `move` renames, `--copy` duplicates, an existing destination is refused. The only removal is a tombstone under `--force`.
- Do not hand-edit a record to change ownership — the file's location *is* the ownership.
- Do not patch a record the app has loaded; the in-memory copy wins and will overwrite it. Use `set_session_title` for renames.
- Out of scope: `~/Library/Application Support/Claude/local-agent-mode-sessions/` is a separate per-account store for agent-mode sessions.

## When triggered implicitly

If a session search came up empty, run `find` before reporting the session as missing — `list_sessions` sees one account's desktop records and nothing else, while `find` sweeps every account plus every CLI transcript. Report where it actually lives (another account, or terminal-only), name it, and offer the direction that fits what the user is doing — do not migrate unprompted.
