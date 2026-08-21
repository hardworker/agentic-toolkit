# Changelog

Per-skill changelogs; each skill follows Keep a Changelog / SemVer independently.

# cf-access

## [1.7.0] — 2026-08-21

**Restart the daemon when updating** (`install.sh`): route labels are read by the proxy.

### Added

- **A direct login explains itself like a proxied one.** `cf-access curl` / `token` / `env` carried no trace, so the page was skipped and the browser opened straight onto Cloudflare — no app, no session, no cause, and no log line to attribute the window to later. The broker now names itself (`cf-access curl pid=…`, session from `CLAUDE_CODE_SESSION_ID`) into the same log, so one `grep sso` covers every window. A login typed at a terminal still goes straight through: a tty proves someone knows who asked.
- **A fixed route can be labelled.** A trailing `# label` on a `proxy` line turns `peer :54239` into `fixed port 8790 ("admin panel MCP")`. Such a client sits on loopback and knows nothing about cf-access, so the route is its only identity.

### Fixed

- **A named session could still show a raw uuid.** The lookup demanded `title` on the desktop record or `name` on the CLI one; a title lands only after the first turn, a terminal session has no desktop record, and the CLI record dies with its pid. Now either id matches, and each store degrades through worktree and directory.

### Changed

- The `sso` line dropped its `— starting browser sign-in for` filler. `sso` already said it.

### Security

- A session id off the environment is validated once, in the broker, before it reaches a world-readable log and a web page.

### Notes

- `selftest.sh` covers all three, and resolves the `node` shim so a faked `HOME` no longer exits 126. Log rotation still absent.

## [1.6.1] — 2026-08-14

### Fixed

- **The sign-in page showed a raw session id instead of the name.** The proxy quoted the session with `q()` for the log line and handed that same quoted string to the page generator, so the lookup compared `"<uuid>"` against `<uuid>` and matched nothing. Raw in the env now, quoted only at the log boundary. The stub broker in `selftest.sh` records what it was handed, so this cannot regress silently.

## [1.6.0] — 2026-08-14

**Restart the daemon when updating** (`install.sh`): the preload goes live at once, only the new proxy strips its new headers.

### Added

- **Every SSO browser window says what caused it** — one line, from the funnel every SSO path crosses:

  ```
  sso https://ci.example.com — starting browser sign-in for GET "/api/jobs"?… ← "pid=8123 ppid=8100 server.mjs" session="<uuid>"
  ```
- **The window opens on a local page** naming app, session and trigger, linking on to Cloudflare. Not an iframe: the IdP sends `X-Frame-Options: DENY`.
- **Clients name themselves** via `x-cf-access-client` / `x-cf-access-session`, and sessions resolve to the name the app shows. Unreached clients show `peer :<port>`.
- **`selftest.sh` grew a proxy harness**: stub broker, fake gated upstream, free ports.

### Fixed

- **An abandoned login wedged every later one, silently.** `cloudflared` leaves a lock behind when killed — which the deadline does — so the next login blocked with no output (63s, against 1s once cleared). Now cleared when no login is running.

### Security

- Request path only, never the query string.
- Script name only when Node runs a script, never under `node -e`.
- `x-cf-access-*` stripped in `forward()` — the namespace, not today's names.
- Wire values quoted and bounded, else a loopback client can forge a log line.
- SSO urls redacted from captured stderr. Never argv, env or headers.

### Notes

- A warm org session mints silently, so an `sso` line with no window is normal. `redact()` untested; log rotation still absent.

## [1.5.0] — 2026-08-13

### Added

- **No login hangs forever.** `cf-access` abandons an unanswered SSO after `CF_ACCESS_LOGIN_DEADLINE`, killing `cloudflared` and the grandchild holding the pipe, and restoring the stashed token. The bound sits in the broker, where every caller routes through.
- **`status` sees the whole config dir**, so the `proxy` routes file appears, and prints the resolved SSO browser by asking `cf-access browser`.
- **`browser.example` is seeded** with the other templates, its placeholder commented out so a seeded copy is inert.

### Changed

- **The suffix allowlist has one implementation** (`cf-access-hosts.cjs`, shared by proxy and preload). It had existed twice and already diverged on freshness. Now cached on a 2s TTL — not a watcher, which would stop every Node process exiting.
- **`install.sh` carries every `CF_ACCESS_*` knob into the plist**, not just `CF_ACCESS_HOLD`.
- **The proxy finds `cf-access` beside itself** (`__dirname`) instead of a hardcoded bin path.
- One `jwt_claim` helper replaces two payload decoders; TTL computed once per read. `forward()` lost its `keepClientAuth` flag. `selftest.sh` reads its browser fixture once.

### Fixed

- **`CF_ACCESS_PROXY_DYNAMIC_PORT` did nothing under launchd** — read for the health check, never written to the plist, so the daemon booted on 8780 and the probe reported failure. Same for `CF_ACCESS_HOSTS_FILE` and `CF_ACCESS_SKEW`.
- **`--bin-dir` outside `~/.claude/bin` broke the non-launchd path**, where nothing sets `CF_ACCESS_BIN`.

## [1.4.0] — 2026-08-03

### Added

- **Every login reports its URL** — the fallback whenever no browser appears. Previously a failed launch left nothing to click.
- **Any Chromium browser**: Chrome, Chrome Beta/Canary, Brave, Edge, Vivaldi, Arc, in that order. `CF_ACCESS_BROWSER_APPS` replaces the search list.
- **The unset case is explicit**: `open` on macOS, `xdg-open` elsewhere.
- Two selftest cases on a stub `cloudflared`: the URL is reported, and handed to the opener.

### Changed

- The two login paths collapsed into one. Same behaviour unconfigured, less code, URL reported either way.

## [1.3.0] — 2026-08-03

### Added

- **Name the SSO browser by account, not by folder.** `CF_ACCESS_BROWSER` accepts `you@work.example` and resolves it to the profile signed in as that account. Folder names (`Profile 2`) are opaque and survive renames, so they are the wrong thing to put in config. A command is still accepted; an unmatched address warns and falls back rather than failing the login.
- **`cf-access browser`** prints the command SSO will use, without triggering a login.
- **`selftest.sh`** covers the four resolution branches. No framework.

## [1.2.0] — 2026-08-03

### Added

- **`browser` config / `CF_ACCESS_BROWSER`** — which browser opens the SSO page. `cloudflared` has no `--no-browser`, but with `open` hidden from `PATH` it prints the URL instead, which is then handed to your command. Read from a file as well as the env, so shell and daemon agree without plumbing it into the plist.
- **`CF_ACCESS_HOLD` persists across installs** — taken from the env, else the plist being overwritten, else the default.

### Fixed

- **`install.sh` could leave the daemon down.** `launchctl bootout` returns before the job is gone, so the following `bootstrap` failed with `Input/output error`. Now waits for the label to disappear, bounded at 4s.

## [1.1.0] — 2026-07-29

### Fixed

- **A request can no longer hang on an interactive login.** `execFile`'s `timeout` sends `SIGTERM`, which `cloudflared` ignores while holding its pipe open — a 120s cap became a 9-minute stall. The deadline now settles the mint itself; the kill is best-effort cleanup. A late success still lands in the cache for the retry.
- **A client that brings its own Access credential is no longer overridden.** Learned gating had been per origin and unconditional, so one credential-less client poisoned every credentialed one on that host.
- **…but a rejected credential still gets service.** If Access refuses the client's own credential the broker takes over, rather than handing back a login page.

### Added

- **`CF_ACCESS_HOLD`** (default 20s) — how long a request waits before a `511` while the login continues; `0` disables waiting.
- **`CF_ACCESS_LOGIN_DEADLINE`** (default 120s) — hard cap on one mint.
- Troubleshooting rows for the three symptoms this release explains.

## [1.0.0] — 2026-07-29

Initial release: keep CLI tools, Node clients and long-running MCP servers authenticated to Cloudflare Access–gated hosts.

### Added

- **`cf-access`** — the broker: `token`, `cookie`, `env`, `curl`, `login`, `list`. Truncates app URLs to their origin, reports token lifetime, refreshes under 10 minutes. `env` uses `env(1)`, so header-name variables may contain hyphens.
- **`cf-access login` purges before it logs in**, since `cloudflared` otherwise returns the cached token. The purged token is stashed and restored on any exit path. Cache files are identified by the token's own `aud`, which a hostname glob would miss under a wildcard policy.
- **`cf-access-proxy`** — localhost fronts injecting a fresh token per request. Dynamic port (8780) takes the upstream from a header; optional fixed `<port> <origin>` routes serve clients that can only take a URL. Caches are per origin, single-flight, with a 60s login cooldown; bodies are buffered so a retry replays a POST byte-for-byte.
- **Learned gating** — the first request goes out bare, and only a login redirect marks the origin gated.
- **`cf-access-preload.cjs`** — `NODE_OPTIONS` shim patching `http`/`https`/`fetch`, so an unmodifiable Node client keeps its real URL. Refuses to patch the proxy itself.
- **Suffix allowlist** (`~/.config/cloudflare-access/hosts`) — domains, not apps. Also the boundary stopping the dynamic port being an open forwarder; a missing file allows nothing.
- **`install.sh`** — symlinks the scripts, seeds config without overwriting, writes the plist with the detected `node` plus explicit `PATH`/`CF_ACCESS_BIN`, loads the agent, health-checks the port. `status` reports links, config, daemon, port, token TTLs; `uninstall` removes only its own symlinks.
- **SKILL.md** — layer-selection table, MCP wiring patterns, and a troubleshooting table per originated status code.

### Security

- Config never carries a token; JWTs pass by env or header only, and never into a transcript, commit or log.
- The proxy binds `127.0.0.1` only, forwarding solely to allowlisted hosts.

# session-migration

## [1.2.0] — 2026-07-29

Preflight the background-agent claim. Importing a session whose background agent was still parked created the desktop record and then crashed the app — `claude --resume` exits 1 with "currently running as a background agent (bg)", which the app reports as "Claude Code crashed" and stamps on the record as `errorCategory: process_crashed`.

### Added

- **Claim detection** — `bg_claim()` looks for a live listener on `/tmp/cc-daemon-<uid>/*/rv/<first-8-of-cliSessionId>.sock` and resolves the holding pids with `lsof`. The claim lives in that socket, not in the job's `state.json`, which is why a job reading `done` / `idle` can still own the session — and why the agents view, which files such a job under completed, offers no Stop control for it.
- **`import` refuses a claimed session** and prints the socket, the holding pids with their command lines, the `kill -TERM` line, and the `--fork-session` alternative. `--force` deliberately does not override: the refusal originates in the CLI, so forcing only reproduces the crash.
- **`resume` warns** on the same condition instead of printing a command that would exit 1, and points at `claude agents` to attach.
- **`job` and `move` refuse a claimed session too**, in `write_job` — the one function both route through. The job dir is keyed by the same `cli[:8]` as the socket, so it is the live daemon's own job dir, and writing the synthesized entry would overwrite a running agent's `state.json` with a fabricated `done` / `idle`: the command would manufacture precisely the missing-Stop-control state that made this bug hard to diagnose.
- **`bg-socket` mark** in `list` / `find` output, plus `hasBgClaim` on every record. The mark reports socket presence only — whether it blocks depends on a live holder, which the commands establish — so it deliberately asserts less than the refusals do. `rv_sockets()` is `lru_cache`d, so one `glob` per process serves the marks and the guards from a single source; `lsof` runs only on the paths that can refuse.

### Notes

- A socket with no listener is reported as stale and only warns. `lsof` matches unix sockets by path name, so a deleted socket whose original holder is still alive is still treated as held — the conservative side of the trade.
- **Re-importing an id deleted earlier in the same app run needs a restart.** `--force` clears the `deleted_<uuid>` tombstone and the import repopulates the main-process map — `list_sessions`, which reads that map via `getAllSessions()`, reports the session present — yet the sidebar still hides the row, so the stale state is the renderer's own list, not the map. Only a relaunch clears it. That split (tool sees it, user does not) is the tell; SKILL.md now says so at the post-import step.

## [1.1.0] — 2026-07-29

Both directions. 1.0.0 only knew about sessions that had a desktop record, which meant it could move a session between accounts but was blind to the 147 terminal-only transcripts on this machine and had nothing to say about reopening a desktop session in the CLI.

### Added

- **CLI transcripts are first-class sessions.** `~/.claude/projects/*/<uuid>.jsonl` is scanned into the same inventory as desktop records, tagged `source: cli`, titled from the transcript's own `ai-title` entry and located by its `cwd`/`gitBranch` header fields. Header-only read, first 400 lines, ~1s for 160 sessions — no cache. `find` and `list` now cover sessions the desktop app has never heard of; `list --source cli|desktop` narrows.
- **`resume`** — the desktop → CLI direction, which needs no migration at all because the transcript is account-agnostic: prints the `cd <cwd> && claude --resume <cliSessionId>` line (plus the `--fork-session` variant). The only genuinely missing piece on that side is the `claude agents` row, which `job` already synthesizes.
- **`import` accepts cli-only sessions**, giving a terminal session a desktop record for the first time — the same deep link, now reachable for transcripts the app's own recovery scan would offer only if no account held a record.
- **Direction table in SKILL.md** — destination (sidebar / terminal / agents view) chooses the subcommand, before the import-vs-move tradeoff table chooses the path.

### Changed

- `accounts` reports the cli-only transcript count alongside the per-account rows.
- `move` refuses cli-only sessions with a pointer to `import` — there is no record to relocate.
- Ambiguity and id resolution work off `cliSessionId` when a record id does not exist.

## [1.0.0] — 2026-07-29

Initial release: recover Claude Code Desktop sessions stranded in another account. Built by reading the desktop app's own session store and `app.asar` loader rather than guessing at the format — the mechanisms below are what the app actually does.

### Added

- **`ccd_sessions.py`** — one script, five subcommands: `accounts`, `list`, `find`, `import`, `move`, `job`. No Workflow tool, no subagents; this is a utility skill, not a pipeline.
- **Fuzzy locator** (`find`) — scores a query against title, worktree name, branch, cwd basename and, for untitled sessions, the first real user message pulled from the transcript. Combines `difflib` ratio, substring hit and token recall, so misspellings and partial names resolve ("advarsarial reveiw" → "Adversarial review", 0.89). `--search-transcripts` greps transcript bodies for when only the content is remembered.
- **Live import** (`import`) — fires the app's own `claude://resume?session=<cliSessionId>` deep link, which builds a desktop record from the CLI transcript in the current account and navigates to it. No restart. Costs the title, model and original timestamps (reset to import time); the skill restores the title via `set_session_title`.
- **Record relocation** (`move`) — moves the `local_<uuid>.json` between account directories, preserving title, branch, worktree, model and permission mode. Requires a full app restart: the session map lives in the desktop main process and is rebuilt only on launch or account switch — there is no file watcher.
- **CLI agents entry** (`job`) — synthesizes `~/.claude/jobs/<8-hex>/{state.json,timeline.jsonl}` so a past *interactive* desktop session appears in the `claude agents` view, which it otherwise never does under any account. Account-agnostic, so it works without migrating. `move` does it automatically.
- **Implicit trigger** — the description tells the agent to sweep other accounts whenever a session search comes up empty, before reporting a conversation as missing.

### Safety

- Never moves the running session; never deletes a record (`move` renames, `--copy` duplicates, an existing destination is refused). The only removal is a deletion tombstone under `--force`.
- `import` and `move` each refuse when the other has already run for that conversation — the two produce different session ids, so doing both duplicates the row in recents.
- Ambiguous fuzzy input (top two scores within 0.12) is refused with candidates printed rather than resolved by guess.
- Confirmation required before `import` (it navigates the user's window) and before a real `move`; `--dry-run` and `job` are free.

# crucible

## [2.1.0] — 2026-08-14

### Changed

- **The verify loop is now an explicit [Ralph loop](https://ghuntley.com/ralph/) over a file**, not a prose loop over the agent's memory. It was four steps and a sentence of exit conditions at the end — a shape you leave by deciding you are done, which after one round of fixes is an easy thing to decide, and which a compaction mid-loop erases the round count, the declined findings and the previous failures from in one go. Each pass now starts by reading the `## Verify` section of `progress.md` (round number, findings already declined and why, last round's failures), appends its own round record *before* evaluating anything, and only then checks three named exits — `clean`, `capped`, `stagnant` — against what it just wrote. None fires and the procedure runs again from step 0; step 4 is explicitly never the end of a round. The report names the exit that fired. Same round caps, same cost. No new artifact: `progress.md` already existed as the build's coordination record and already survived compaction, so the loop writes a section of it — which as a side effect makes the verify phase resumable by a fresh context, the one place in crucible where that is worth having.

## [2.0.1] — 2026-08-14

### Fixed

- **The skeptic panel ran inside the context it exists to be independent of.** A field run (`/crucible --auto`, Claude Code Desktop) spawned zero agents: recon, all three lenses, the defender and both review angles happened in the main loop, and the report never said so. The host's own system prompt carries "do not call the AgentTool unless the user requested it", which outranks skill text; the ground rule's capability-conditional phrasing ("if your environment can spawn fresh isolated agents… every step also works single-loop") read as permission to resolve the tension by not spawning. The run's own reasoning names both halves of it. The rule now states that invoking crucible **is** the user asking, restricts the fallback to a spawn mechanism that is absent or actually fails, and makes the report name any phase that took it — a silent downgrade to one context grading its own homework is the failure mode worth surfacing, since the output looks identical either way.

## [2.0.0] — 2026-08-13

A pure skill. The pipeline existed twice — a 647-line Workflow script and a sequential playbook — and every change had to land in both; nothing in the design actually needed deterministic control flow, since the gates are conversations and the loops are bounded by counts a paragraph can state. One SKILL.md is now the whole skill, which also means it runs wherever the Agent Skills standard does instead of only where the Workflow tool exists. The same pass fixed both ends of the pipeline: nobody was interrogating the user before the panel spent tokens, nobody was defending the idea against the skeptics, nothing ever looked at the diff a second time, and no phase ever deleted a line.

### Added

- **Phase 0 — grill** (interactive, zero agents). Restate the idea, then attack it *to the user*: ≤4 design-changing questions per round, ≤2 rounds, batched. Vague answers get re-asked once, then become recorded unknowns; the rest enter the brief verbatim as `source: user`. The cheapest place to kill a bad premise is the sentence that states it, and the panel can only attack claims the brief contains. Skipped under `--auto`.
- **Defender step** between the panel and the debate gate (skipped at `low`). One agent tries to refute each consolidated challenge in the actual files — refutation, the verification pattern the design already uses on high findings, not another round of debate. Killed challenges become one-liners in the report; `needs-user` product calls are exempt however well argued.
- **Verify loop** replaces the one-shot test-then-review phase: `suite → fix failures → review → refute → fix confirmed`, repeated until a round comes back green and clean. Bounded by the effort cap and a stagnation breaker — identical failures or findings two rounds running means report, not grind. A fix that introduces its own defect used to ship unreviewed.
- **Simplification as a second review angle.** Everything upstream pushes toward addition (skeptics raise risks, reviewers request fixes, fix rounds add guards); nothing ever removed a line. Every verify round now reviews the diff from both ends in parallel — correctness (≤6 merge-blocking findings) and simplification (≤4) — as two agents, since one reviewer holding both mandates dilutes into neither. The simplification mandate covers surface waste (dead code the change introduced, one-caller indirection, speculative options) *and* over-built structure, walked down a YAGNI ladder: does the construct need to exist at all → does the repo already have the helper it reimplements (cited `file:line`) → does the stdlib/platform cover it → would plain code beat the abstraction. Findings must name the concrete smaller shape with the same behavior; "rewrite it nicer" is not a finding. Deletions land inside the loop, so the next round's suite and reviewer verify them. A simplification that would change behavior, undo a confirmed fix, reach outside the diff or remove something the files prove load-bearing is refuted like any other finding; declined ones are recorded and never re-raised.

### Removed

- **`crucible.mjs`** and the Workflow path, **`PLAYBOOK.md`** (absorbed into SKILL.md), and **`eval/crucible-smoke.mjs`** — with no script there is no control flow to stub-test. Crucible is field-run-validated from here.
- **The JSON result contract and budget accounting.** Fan-outs no longer scale to a token budget; the effort level alone sets the counts, and token discipline is stated as caps (≤10 assumptions, ≤8 tasks, ≤6 findings per round) instead of computed. Statuses collapse to `done` / `done-with-findings` / `challenged` / `blocked`.
- **`--cwd`, `--focus`, `--phase`.** `--cwd` and its path plumbing served the script; emphasis rides along in the idea text; `--phase` bought a resume protocol and a run-dir discovery rule for a case that is usually "continue in this session". Arg surface is now the idea, `--auto`, `--effort`.

### Changed

- **Isolated agents only where isolation is the mechanism** — recon (read-only, keeps the largest read of the run out of the loop that must survive to the last verify round), each skeptic lens in parallel, the defender, each review angle in each round. Consolidation, plan drafts, implementation and the suite run in the main loop, and every step has a single-loop fallback.
- **Artifacts moved out of the repo** — `brief.md`, `challenges.md`, `plan.md`, `progress.md` go to the session scratchpad, else `~/.crucible/<repo>/<timestamp>/`. No more `.git/info/exclude` handling, and the reviewer's `git diff` is exactly the change.
- **Three effort levels** — `low | medium | high` (`xhigh`/`max` accepted as aliases). With no script to pass reasoning tiers through, the top two levels bought one extra refute vote. Presets: lenses 2/3/4, competing plans 2/2/3, defender off/on/on, verify rounds 1/2/3, refute votes 0/2/3.
- **Lens count unified on the script's presets** (2/3/4) — the playbook ran all four lenses at `medium`, the script ran three.

## [1.1.0] — 2026-07-17

Args and docs aligned with adversarial-review.

### Added

- **Effort levels** (`--effort low|medium|high|xhigh|max`, default `medium`) — the same depth scale as adversarial-review and `/code-review`: one preset table drives skeptic count (2/3/4), planner count (2/2/3), test-fix rounds (1/2/3), refute votes (skipped-with-annotation at `low`, 2-vote unanimous-rejects at medium/high, 3-vote majority-rejects at `xhigh`+), and agent reasoning tiers (judges `medium`→`max`, workers `low`→`max`, suite runner pinned at `low`). The budget floor still applies regardless of effort. Result reports `effort`.

### Changed

- **`--thorough` removed** — `--effort high` replaces it (one depth knob across the toolkit).
- **Docs aligned to the sibling's format** — SKILL.md argument table converted to three columns (user input → JSON arg → meaning), playbook flag mapping rewritten in effort terms, cost line notes the effort effect.

## [1.0.0] — 2026-07-16

Initial release: end-to-end build pipeline (idea → tested code) that debates the user's assumptions before building. Designed from a survey of the 2024–2026 multi-agent literature (Debate-or-Vote, Cost-of-Consensus, SycEval, MAST, Cognition/Anthropic orchestration guidance, SWE-bench ensembling analyses); the load-bearing citations live in ARCHITECTURE.md.

### Added

- **Phase-parameterized Workflow script** (`crucible.mjs`) — `phase: surface | plan | develop | test | full`; the main thread chains invocations with a debate gate after surface and a go/no-go gate after plan; `full` is the autonomous mode that halts (`challenged`) instead of guessing whenever a human ruling is needed. Deliberately no dry-run flag: a plan-only run is just the surface and plan invocations without the rest; report-only review of existing changes is adversarial-review's job.
- **Skeptic panel (surface phase)** — 2–4 isolated lenses (feasibility / necessity / scope / adversary) attack every brief assumption with file evidence; no cross-talk between skeptics; assumptions passed unattributed (naming the user's position measurably increases agreement with it); uncertainty maps to `shaky`, never `holds`; a consolidating judge file-verifies contested verdicts.
- **Competing plans + verifying judge (plan phase)** — 2–3 forced-apart planner angles (minimal / robust / refactor-first); the judge spot-checks file claims by opening files, synthesizes one plan of ≤ 8 tasks, keeps test-first ordering when test infra exists, and surfaces `planChallenges` for genuine product calls.
- **Sequential develop phase** — one implementer agent per task in dependency order, each seeing the whole plan, completed-task summaries, and deviations; per-task test evidence required; `blocked` stops the run instead of improvising; out-of-plan file touches are logged.
- **Test + hostile review phase** — full suite with a bounded fix loop (stagnation fingerprint breaker), fresh-context reviewer hunting merge-blocking defects/design/acceptance-gaps/hollow-tests, 2-vote refute panel on high findings, auto-fix of confirmed high/medium findings with one suite re-run.
- **Budget as a first-class mechanism** — fan-outs scale to the workflow token budget (reserve-half rule, ~70k/agent from sibling field data), every phase boundary stops cleanly as `budget-exhausted`, and the result reports actual per-phase spend (`result.tokens`).
- **Sequential fallback (`PLAYBOOK.md`)** — the same pipeline as a portable single-loop protocol per the Agent Skills open standard: no tool names, capability-conditional wording, `.crucible/` phase artifacts as compaction-proof memory. Codex CLI picks it up from `.agents/skills/`; `codex review` slots in as the fresh-eyes reviewer.
- **Stub-runtime smoke test (`eval/crucible-smoke.mjs`)** — executes the real script's control flow with canned agent responses (30 checks: chaining, gates, blocked tasks, stagnation, refute kills, budget floors, error surfacing) at zero token cost.

# adversarial-review

## [3.0.0] — 2026-08-19

### Removed

- **Four flags: `--base`, `--iterations`, `--rounds`, `--cwd`** — none had ever been reached for, and each was either a duplicate or a dial on a constant. `--base <ref>` duplicated the bare-ref target (`/adversarial-review develop`), which stays. `--iterations` and `--rounds` tuned caps whose loops already stop earlier on their own — agreement, stagnation, concession — so both are now fixed constants of 3 and the flags' only real job (backstop) is intact. `--cwd` reviewed a checkout outside the session cwd; start the session in that repo instead. Its removal also deletes the two `[when --cwd]` conditionals from the stage prompts and `-C` from the Codex invocation.
- **The legacy aliases `--strict` and `--repo`** (for `--effort low` and `--cwd`). `xhigh`/`max` still parse and mean `high`, since `--effort` shares its axis with `/code-review`.

## [2.0.2] — 2026-08-14

### Fixed

- **Same subagent-suppression hole as crucible 2.0.1**, prophylactically. A host system prompt that withholds subagents until the user asks for them can silently turn every "spawn one `general-purpose` agent" into the orchestrator doing it inline — which for this skill means the reviewer reads the target it must never see. The preamble now says the invocation is the request, and that an absent spawn mechanism is an `error`, not an invitation to self-review. No field failure observed here; the wording was already imperative, but it did not neutralize the rule it was competing with.

## [2.0.1] — 2026-08-14

### Removed

- **Eval harness (`eval/`)** — the seeded-bug fixture protocol and `score.mjs`. Added in 1.1.0 to score pipeline changes for recall / false positives / cost, it never had a fixture built for it, so it measured nothing across every release since, the 2.0.0 rewrite included. The skill itself is unchanged. Measuring protocol changes is still the right standard; the protocol is in git history for whoever builds the first fixture.

## [2.0.0] — 2026-08-13

Plain skill, and a real debate. SKILL.md is now the whole pipeline, executed by the main agent loop — no Workflow tool, no multi-agent opt-in. The two reviewers now argue to a conclusion instead of trading one round of verdicts, while the machinery around them got smaller by three unmeasured mechanisms.

### Added

- **The debate loops until the reviewers agree, deadlock, or hit `--rounds`** (default 3). Round 1 is cross-examination as before. Later rounds carry only the findings still disputed: each side answers the attacks on its own findings and re-judges the defences it received, one call per side per round. Findings an author withdraws are dropped before the judge and reported separately; the rest reach the judge tagged with how they settled.
  Two rules keep this from becoming a race to agree, which is the documented failure mode of debating to consensus ([The Cost of Consensus](https://arxiv.org/html/2605.00914v1), [Debate or Vote](https://arxiv.org/abs/2508.17536)): conceding requires citing the file evidence that changed your mind — deferring to the other reviewer is explicitly not a resolution — and repeating a claim without new evidence is classified as deadlock rather than argument, which ends the loop instead of extending it. The judge is told that agreement reached mid-debate is weaker evidence than two reviewers finding the same thing independently, and that deadlocks are its to arbitrate in the files.
  This reinstates, narrowly, the meta-review phase 1.0.0 removed. That version made *every* finding take a rebuttal round and the judge still had to re-verify in the files; this one runs only where the two models actually disagree, so a debate that agrees in round 1 costs exactly what one-round cross-examination cost.

### Removed

- **`adversarial-review.mjs`.** SKILL.md carries the scope rules, every stage prompt, the loop guards and the report format.
- **The refute panel.** It spent 2–3 agents on every uncorroborated high finding, and its refuters saw only the finding — not the critic's reasoning, not the debate record — so two low-context agents could overrule the one that had seen everything. Its threshold (`floor(votes/2)+1`) also made rejection *easier* at higher effort, where wide-net makes findings more numerous. Never measured, and the only uncorroborated high in the field record was real. The judge's tiering absorbs its job in one line: on a high only one side raised, spend the file read trying to refute it.
- **Two effort levels.** `xhigh` and `max` differed from `high` only by an issue cap once the reasoning-tier axis went away. Three levels remain; both names still parse and mean `high`.
- **`--strict`**, which was `--effort low` minus the model choice, and existed only to be arbitrated against it ("strict wins over wide net"). Still parses, means `--effort low`. Same call the repo made dropping `--thorough` in 1.3.0.
- **The `duplicateOf` tagging channel.** It injected one side's findings into the other side's critic — the one agent whose value is being uncontaminated — and then spent a clause telling it not to adopt them. The judge merges duplicates from the threaded record, which it already had.
- **The `impact` field**, folded into `description` ("say who or what it affects"). Severity is already merge-anchored and the description already requires a failure scenario; this was the third statement of blast radius, carried through four stages.
- **The undocumented `files` argument** and the legacy bare keywords (`fix`, `solo`, `iterations <n>`, `base <ref>`). They existed for JSON callers of the Workflow script, which no longer exists. `--repo` still maps to `--cwd`.

### Changed

- **The Codex legs no longer cost an agent.** The main thread runs `codex exec` itself, so Codex's answers reach the judge verbatim instead of through a transcribing runner. Scope stays an agent: resolving a target is trivial work, but doing it inline puts the diff in the context that lives for the whole run and turns "the orchestrator never reviews" from a boundary into an instruction. A one-round debate is 4 subagents plus 2 Codex calls, and 2 more calls per extra round.
- **`codex exec` now runs with `-o`, `--output-schema` and `-C`.** `-o` plus redirecting the rest keeps Codex's reasoning transcript out of the orchestrator's context; `--output-schema` states the expected answer shape; `-C` sets the working root without a `cd <root> &&` prefix.
- **JSON output contracts replace `StructuredOutput` schemas** on the Claude legs, one shared shape with the Codex legs. A malformed answer is re-asked from the same agent rather than re-running the stage; twice malformed reports `error`.
- **Effort selects a model, not a reasoning tier**, since a plain skill's agent spawns expose `model` and not `effort`. 1.x ran the judge above the reviewers at `low`/`medium` and level with them from `high` up, so the presets keep it at or above them at every level.
- **Loop guards are now the main thread's bookkeeping** — mutation guard, stagnation fingerprint and anti-anchoring memory are instructions rather than script control flow. Enforcement is no longer deterministic. The orchestrator also holds both Codex answers now, which the scope agent and `-o` keep to the findings themselves rather than the diff or the reasoning behind them.
- **The result JSON is written to a temp file** instead of being returned by the Workflow runtime, once at the end of the run.

### Fixed

- **The mutation guard no longer trips on the target's own dirt.** It compares the fixer's `changedFiles` against a `git status --porcelain` snapshot taken before the fixer ran; previously a `working-tree` target — the default — listed every uncommitted file as the fixer's own and halted iteration 1 as `scope-violation`. Present in 1.x since the guard was added.
- **Critics are capped at 5 missed issues**, the one fan-out in the pipeline with no bound on its input.

### Note

This pipeline has not been run. The 332k/628k token figures and the 18/32-minute timings in this changelog are 1.0.0 measurements on PR #208, and no `eval/` fixture for this skill has ever been built.

## [1.3.1] — 2026-07-17

### Changed

- **`--repo` renamed to `--cwd`** (`cwd` JSON arg), matching crucible's flag for the same concept. Legacy `--repo` / `repo` still map, so existing callers keep working.

## [1.3.0] — 2026-07-16

### Added

- **Effort levels** (`--effort low|medium|high|xhigh|max`, default `medium`), the same depth scale as the built-in `/code-review`: low/medium buy precision, high and above buy coverage. One preset table drives the whole pipeline — per-reviewer issue cap (5→25), finding bar (`low` = strict merge-blocking bar; `high`+ = wide net, reviewers also raise labeled suspicions for the debate to filter), reviewer/critic/judge reasoning tiers, and the refute panel (skipped-with-annotation at `low`, 2 votes unanimous-rejects at medium/high, 3 votes majority-rejects at xhigh+). Breadth enters at the cheapest stage; the cross-examination → judge → panel chain keeps output precision. `--strict` composes and wins over wide-net. `medium` is the pre-1.3 pipeline unchanged; result now reports `effort`.

## [1.2.0] — 2026-07-12

### Changed

- **Flag-style arguments**, matching built-in Claude Code commands: `--base <ref>`, `--fix`, `--iterations <n>`, `--strict`, `--no-codex`, `--repo <path>`; positional target (`working-tree` or a path); remaining free text is still the reviewer focus.
- **`solo` renamed to `codex: false`** (`--no-codex`) — the old name didn't say what it did. Bare legacy keywords (`fix`, `solo`, `iterations <n>`, `base <ref>`) still parse, and old JSON args (`solo`, `base`, `changeDir`, `mode`) still map, so existing callers (e.g. the OpenSpec schema) keep working.

## [1.1.0] — 2026-07-12

Precision and cost-control upgrades, informed by a survey of current adversarial-review research and tooling (Refute-or-Promote stage-gating, TriAdReview, the "Do More Agents Help?" protocol study, dementev-dev's skill, production reviewer FP benchmarks). Every mechanism is bounded — nothing adds a standing per-run cost.

### Added

- **Baseline-diff rule** — diff reviewers may only flag issues the change introduces or materially worsens, and must check the merge-base before reporting anything possibly pre-existing. Kills the false-positive class that dominated the PR #208 field test at the cheapest point in the pipeline.
- **`duplicateOf` tagging** — critics see a compact list of their own side's findings and tag cross-model duplicates during cross-review, making the judge's `both` labels bookkeeping instead of inference.
- **`impact` field + merge-anchored severity** — every finding states its blast radius in one sentence; `high` is defined as "a maintainer would block the merge" to counter severity inflation.
- **Tiered judge verification** — the judge file-verifies disputed high/medium findings; lows are decided on the debate record alone (unvetted lows are rejected, precision over volume).
- **Refute panel** — each confirmed high finding lacking cross-model corroboration gets two fresh refuters; 2/2 refuted rejects it, 1/2 annotates it contested. Bounded: corroborated highs skip it.
- **Mutation guard (fix mode)** — the fixer reports every touched file; edits outside the confirmed findings' files stop the run as `scope-violation`.
- **Anti-anchoring memory (fix mode)** — iteration 2+ reviewers receive the confirmed-and-fixed list and hunt what was missed instead of re-debating it.
- **`strict` mode** — end-to-end low-noise switch: only merge-blocking findings survive reviewers and judge, issue cap drops to 5.
- **Eval harness (`eval/`)** — seeded-bug fixture protocol plus `score.mjs` for recall / false-positive / cost regression scoring of pipeline changes.

## [1.0.0] — 2026-07-12

Initial public release as an installable skill (previously a personal `~/.claude/workflows/` script, built 2026-07-03 after [alecnielsen/adversarial-review](https://github.com/alecnielsen/adversarial-review)).

### Changed — leaner debate (~40% fewer tokens on comparable diffs)

- **Removed the meta-review phase.** Previously each reviewer answered the critique of its own findings (2 extra agents re-reading everything each iteration). Now the synthesis judge adjudicates disputes directly and is required to verify every disputed *or uncritiqued* finding in the actual files before confirming or rejecting it. 8 agents/iteration became 4–6.
- **Per-issue threading for synthesis.** The judge receives each finding merged with its critic's verdict, instead of six overlapping debate documents.
- **Compact JSON everywhere.** Debate payloads embedded in prompts are no longer pretty-printed.
- **Output caps.** At most 10 issues per reviewer, descriptions ≤ 3 sentences, critique reasoning ≤ 2 sentences.
- **Codex runner agents run at low reasoning effort** — they only shell out to the Codex CLI and transcribe its answer.

### Changed — one unified review path

- The `mode` / `base` / `changeDir` argument trio is replaced by a single **`target`**: `auto` (uncommitted changes if any, else branch diff vs. the default branch), `working-tree`, any git ref, or a directory/file path reviewed as-is. Planning documents (OpenSpec artifacts, specs, proposals) go through the same pipeline as code; document-specific review criteria (contradictions, ambiguity, task/spec coverage) are folded into the standard defect definition. Legacy argument names still map onto `target` for old callers.

### Added — decision challenging

- Findings are now typed **`defect`** or **`design`**. Reviewers are explicitly instructed to attack the author's decisions — data flow, abstractions, dependencies, algorithms, API shapes — and every design finding must name a concrete, materially better alternative. The synthesis judge may only confirm a design finding after checking the alternative is feasible in that codebase, and may not discard confirmed ones as taste.

### Added

- **`repo` argument** — review a repository outside the session's working directory (e.g. a PR checked out in another worktree). All git commands and the Codex CLI run against that root.
- **`solo` flag** — skip the Codex leg for a cheaper single-model run.
- **Self-critique fallback.** When Codex is unavailable (or in `solo` mode), a fresh Claude agent with no shared context cross-examines the findings, so nothing reaches the synthesis judge uncontested.
- **Codex code-mode recovery.** If the Codex CLI fails with a missing `codex-code-mode-host` (Homebrew cask 0.144.0 shipped without it), the runner retries once with `--disable code_mode_host`.
- **Distribution.** Repo is installable both via `npx skills add` (top-level `skills/`) and as a Claude Code plugin marketplace (`.claude-plugin/`).

### Field-tested

- 2026-07-11, solo run (Codex CLI broken): PR #208 of a private repo, 66 files. 7 confirmed findings, 332k subagent tokens, 18 min, 4 agents.
- 2026-07-12, full duo run, same PR: 13 confirmed / 3 rejected findings, including a HIGH design finding (prompt-only privilege confinement) that the Claude leg missed in both runs, and 3 Codex findings killed in cross-review with merge-base evidence. 628k subagent tokens, 32 min, 6 agents. Token cost tracks debate volume (finding count), not phase count.

### Prehistory (2026-07-03, unreleased `~/.claude` version)

Independent Claude + Codex reviews → cross-review → meta-review → synthesis → optional fix loop with stagnation circuit breaker; separate `code` and `proposal` modes; ~592k tokens / 8 agents per iteration on its verification run.
