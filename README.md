# agentic-toolkit

Personal agent toolkit. See [ARCHITECTURE.md](ARCHITECTURE.md) for how the pipelines work and [CHANGELOG.md](CHANGELOG.md) for history. Four skills:

## adversarial-review

Adversarial Claude-vs-Codex debate review of any target — branch diff, working tree, or documents (specs, proposals, plans). Hunts real defects **and** challenges design decisions, approaches, and implementation paths.

Pipeline (4 subagents + 2 Codex calls, plus 2 calls per extra debate round):

```
Scope → [Claude review ∥ Codex review] → debate, both ways, until agreed or stuck → Synthesis judge → (Fix loop)
```

- Both reviewers work independently, then argue: round 1 is cross-examination, later rounds run only on findings still disputed, until they agree, stop moving, or hit `--rounds` (default 3).
- Conceding takes cited file evidence — deferring to the other reviewer isn't a resolution, and repeating a claim without new evidence is scored as deadlock, so the loop can't just converge on whoever argues hardest.
- The synthesis judge arbitrates deadlocks and re-verifies in the actual files. Two reviewers finding something independently counts for more than agreement reached mid-argument.
- Findings are typed: `defect` (concrete failure scenario required) or `design` (concrete better alternative required).
- Codex leg degrades gracefully — if the Codex CLI is missing/unauthenticated, the run continues single-model, with a fresh-context critic standing in so nothing reaches the judge uncontested.

### Usage

```
/adversarial-review                            # auto: uncommitted changes, else branch diff vs default branch
/adversarial-review working-tree               # uncommitted changes only
/adversarial-review --base develop             # branch diff vs merge-base with develop
/adversarial-review openspec/changes/foo/      # review documents as they stand
/adversarial-review --fix --iterations 2       # apply confirmed fixes, re-review, up to 2 rounds
/adversarial-review --rounds 5                 # let the two models argue longer before the judge steps in
/adversarial-review --no-codex                 # skip Codex leg (cheaper single-model)
/adversarial-review --effort low               # cheap precision pass: merge-blocking findings only
/adversarial-review --effort high              # widest net, strongest model
/adversarial-review --cwd ~/src/other-repo     # review a checkout outside the cwd
/adversarial-review focus on the retry logic   # free text becomes reviewer focus
```

A plain skill — SKILL.md *is* the pipeline, run by the main agent loop, with no orchestrator script.

Requires: an agent that can spawn fresh subagents, read/edit files and run shell commands; only Claude Code has been exercised. Optional: [Codex CLI](https://github.com/openai/codex) (`codex login`) for the second model.

## crucible

End-to-end build pipeline named after the vessel ore is tested in under fire: an idea goes in, gets grilled, gets its assumptions attacked by a skeptic panel, survives a debate with you, becomes a judged plan, then tested code. One SKILL.md, no orchestrator script.

```
Grill → recon → [skeptic lenses ∥] → consolidate → defend → ══ debate gate ══
      → competing plans → judge → ══ plan gate ══ → sequential develop
      → ⟳ suite + [correctness review ∥ simplification review] + refute + fix ⟳
```

- The grill comes before anything costs tokens: ≤4 design-changing questions per round, 2 rounds max, and the answers become the assumptions the panel attacks.
- Skeptics attack every assumption with file evidence (feasibility / necessity / scope / adversary lenses), assumptions handed over unattributed; a defender then tries to refute each challenge in the files, so only survivors reach you. Your rulings are settled, never re-litigated.
- Plans compete (minimal vs robust vs refactor-first); a judge file-verifies their claims and synthesizes one, test-first when test infra exists.
- Implementation is sequential with per-task test evidence, then the verify loop runs suite → review → refute → fix until it comes back green and clean, with a stagnation breaker.
- Each round reviews the diff from two independent angles: correctness (defects, design errors, unmet criteria, hollow tests) and simplification — surface waste (dead code, one-caller indirection, speculative options) plus over-built structure, walked down a YAGNI ladder: needs to exist at all → repo already has it → stdlib/platform covers it → plain code beats the abstraction. One reviewer asked for both dilutes into neither, and a simplification that changes behavior or undoes a confirmed fix is refuted like any other finding.
- Phase artifacts are written outside the repo, so the reviewer always sees a clean working tree.

### Usage

```
/crucible add rate limiting to the public API      # grill → debate → plan gate → build → verify loop
/crucible --auto migrate configs to TOML           # no human: no gates; halts instead of guessing a ruling
/crucible --effort low ...                         # cheap pass: 2 lenses, 2 plans, no defender, 1 verify round
/crucible --effort high ...                        # wide net: 4 lenses, 3 plans, 3 verify rounds, 3 refute votes
```

Requires: any agent that can read files, edit files and run shell commands. Isolated subagents run recon, the skeptic lenses, the defender and each review round; single-loop is the fallback for a runtime that has no spawn mechanism, not a preference, and the report names any phase that took it.

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

If a background agent still holds the session, `claude --resume` exits 1 and the desktop app shows "Claude Code crashed" over the record it just created. The claim is a socket, not a status, so a job that reads `done` in `claude agents` can still own it — and that view then offers no Stop control. `import` and `resume` check for this first and print the holding pids; `--force` will not push past it. `job` and `move` refuse as well — they would otherwise overwrite the live agent's job state with a fake `done`, which is what removes its Stop control in the first place.

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
- A client that brings its own credential (service token, cookie) is forwarded untouched; the broker only steps in when Access rejects it. No request waits on a human longer than `CF_ACCESS_HOLD` (default 20s) — it gets a `511` while the login finishes in the background, so the retry succeeds.
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

For Codex CLI, copy or symlink the skill directories into `.agents/skills/`.
