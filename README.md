# agentic-toolkit

Personal agent toolkit. See [ARCHITECTURE.md](ARCHITECTURE.md) for how the pipelines work and [CHANGELOG.md](CHANGELOG.md) for history. Four skills:

## adversarial-review

Adversarial Claude-vs-Codex debate review of any target — branch diff, working tree, or documents (specs, proposals, plans). Hunts real defects **and** challenges design decisions, approaches, and implementation paths.

Pipeline (one iteration, 4–6 subagents):

```
Scope → [Claude review ∥ Codex review] → [cross-examination ∥] → Synthesis judge → (Fix loop)
```

- Both reviewers work independently, then attack each other's findings.
- The synthesis judge re-verifies every disputed finding in the actual files before confirming.
- Findings are typed: `defect` (concrete failure scenario required) or `design` (concrete better alternative required).
- Codex leg degrades gracefully — if the Codex CLI is missing/unauthenticated, the run continues single-model.

### Usage

```
/adversarial-review                            # auto: uncommitted changes, else branch diff vs default branch
/adversarial-review working-tree               # uncommitted changes only
/adversarial-review --base develop             # branch diff vs merge-base with develop
/adversarial-review openspec/changes/foo/      # review documents as they stand
/adversarial-review --fix --iterations 2       # apply confirmed fixes, re-review, up to 2 rounds
/adversarial-review --strict                   # low-noise: only merge-blocking findings
/adversarial-review --no-codex                 # skip Codex leg (cheaper single-model)
/adversarial-review --effort low               # cheap precision pass: merge-blocking findings only
/adversarial-review --effort max               # widest net, strongest reasoning, 3-vote panel
/adversarial-review --cwd ~/src/other-repo     # review a checkout outside the cwd
/adversarial-review focus on the retry logic   # free text becomes reviewer focus
```

Requires: Claude Code with the Workflow tool. Optional: [Codex CLI](https://github.com/openai/codex) (`codex login`) for the second model.

## crucible

End-to-end build pipeline named after the vessel ore is tested in under fire: an idea goes in, gets its assumptions attacked by a skeptic panel, survives a debate with you, becomes a judged plan, then tested code. Budget-scaled at every fan-out.

```
Recon → [skeptic panel ∥] → consolidate → ══ debate gate ══
      → [competing plans ∥] → plan judge → ══ plan gate ══
      → sequential develop → test suite + fix loop → hostile review → refute votes → fix
```

- Skeptics attack every assumption with file evidence (feasibility / necessity / scope / adversary lenses); you rule on the survivors — rulings are settled, never re-litigated.
- Plans compete (minimal vs robust vs refactor-first); a judge file-verifies their claims and synthesizes one, test-first when test infra exists.
- Implementation is sequential with per-task test evidence; a fresh hostile reviewer plus a 2-vote refute panel gate the result.
- Works without the Workflow tool too: [PLAYBOOK.md](skills/crucible/PLAYBOOK.md) is the same pipeline as a sequential protocol for Codex CLI or any Agent-Skills-compatible agent.

### Usage

```
/crucible add rate limiting to the public API      # gated run: debate → plan gate → build → test
/crucible --auto migrate configs to TOML           # one-shot; halts instead of guessing when a ruling is needed
/crucible --effort low ...                         # cheap pass: 2 skeptics, 2 planners, no refute panel
/crucible --effort high ...                        # wide net: 4 skeptics, 3 planners, 3 fix rounds
/crucible --phase test                             # re-run a single phase
/crucible --cwd ~/src/other-repo ...               # build in a checkout outside the cwd
```

Requires: Claude Code with the Workflow tool for the orchestrated path; anything that can read/edit files and run shell commands for the playbook path.

## session-migration

Finds any past session and puts it where you want it. Two things hide sessions from you: Claude Code Desktop scopes its records per account, so an account switch buries everything created before it; and terminal sessions never get a desktop record at all. Both are invisible to `list_sessions` and `search_session_transcripts` — the skill sweeps every account **and** every CLI transcript on disk. macOS only.

It also fires implicitly: when a session search comes up empty, look in the other accounts and the CLI before telling the user the conversation does not exist. Names are matched fuzzily, so a half-remembered or misspelled title is enough.

Where you can send a session:

| Destination | How | Notes |
|---|---|---|
| Desktop sidebar, now | `import` | `claude://resume?…` deep link → the app's own import. Loses title, model, original timestamps |
| Desktop sidebar, intact | `move` | relocates the record file; keeps everything; needs a full app restart |
| Terminal | `resume` | prints `cd … && claude --resume …`; the transcript was always there |
| `claude agents` view | `job` | synthesizes the background-job entry that interactive sessions never get |

`import` and `move` are mutually exclusive — they produce different session ids, so running both duplicates the row in recents. Each refuses when the other has run.

### Usage

```
/session-migration                              # everything not in this account's sidebar
/session-migration astro theme                  # fuzzy-find across accounts and CLI transcripts
/session-migration the one about metro ports    # --search-transcripts when only content is remembered
/session-migration <name> --import              # into the desktop app now
/session-migration <name> --move                # into the desktop app intact, needs a restart
/session-migration <name> --resume              # reopen it in the terminal
```

Requires: Python 3, macOS, Claude Code Desktop.

## cf-access

Keeps everything on the machine authenticated to Cloudflare Access–gated hosts. An Access app whose policy allows only an IdP has no service-token path, so the JWT comes from a browser SSO round-trip and lives about a day — which means any client that reads its credential once at startup (most MCP servers, any daemon) works for a day and then dies with a login redirect that looks nothing like an auth error.

Three layers; pick by what the client can do:

| The client can | Use | Renewal |
|---|---|---|
| take a header/env on every invocation | `cf-access token` / `cookie` / `env` / `curl` | per invocation |
| only be pointed at a URL (any language) | proxy fixed port | per request, by the proxy |
| be a Node process with no config surface | `NODE_OPTIONS=--require …/cf-access-preload.cjs` | per request, by the proxy |

- One browser tap warms the whole org: `cf-access login` refreshes every configured app, minting the rest silently.
- The proxy **learns** which origins are gated — the first request goes out bare, and only a Cloudflare login redirect makes it mint. Non-gated hosts never trigger SSO.
- The allowlist is a **domain suffix** list, so an app added under the domain next month needs no config; that same list is what keeps the loopback port from being an open forwarder.
- `install.sh status` is the one diagnostic — links, config, daemon, port, per-app token TTL — because "no token", "daemon down" and "host not allowed" look identical from the client.

### Usage

```
<skill-dir>/install.sh                    # symlink scripts, seed config, load the launchd agent
<skill-dir>/install.sh status             # what is wired, what is stale
<skill-dir>/install.sh uninstall          # unload and unlink; keeps config and tokens
cf-access login                           # one tap, every configured app
cf-access curl https://ci.example.com/…   # authenticated request
cf-access env <app> <HEADER_VAR> -- <cmd> # launch an MCP server with a fresh token
```

Requires: `cloudflared`, Node. macOS for the launchd agent; the broker and `curl` mode work anywhere `cloudflared` runs.

## Install

Via [skills.sh](https://skills.sh):

```
npx skills add hardworker/agentic-toolkit
```

Via Claude Code plugin marketplace:

```
/plugin marketplace add hardworker/agentic-toolkit
/plugin install agentic-toolkit@agentic-toolkit
```

For Codex CLI, copy or symlink the skill directories into `.agents/skills/` — crucible runs its playbook path there.
