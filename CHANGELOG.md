# Changelog

Per-skill changelogs; each skill follows Keep a Changelog / SemVer independently.

# cf-access

## [1.0.0] — 2026-07-29

Initial release: keep CLI tools, Node clients and long-running MCP servers authenticated to Cloudflare Access–gated hosts. Packaged from a working local setup that had been running as loose scripts in a bin directory; every mechanism below is there because the obvious version of it failed in practice.

### Added

- **`cf-access`** — the broker: `token`, `cookie`, `env`, `curl`, `login`, `list`. Truncates app URLs to their origin (cloudflared caches per hostname, so a path misses the cache), reports remaining token lifetime, and refreshes anything under 10 minutes of life. `env <app> <VAR> -- <cmd…>` uses `env(1)` rather than `export` so header-name variables may contain hyphens.
- **`cf-access login` purges before it logs in.** `cloudflared access login` hands back the cached app token even seconds from expiry, so a refresh without a purge is a no-op. The purged token is stashed and restored on any exit path — including a timeout or Ctrl-C — so a failed refresh cannot cost a browser-less machine a usable token. Cache files are identified by the token's own `aud` claim, because a wildcard-policy app lands in a filename a host-name glob would miss.
- **`cf-access-proxy`** — localhost HTTP fronts that inject a fresh `cf-access-token` per request, for clients that snapshot their credential at startup and cannot renew it. A dynamic port (default 8780) takes the upstream from an `x-cf-access-upstream` header; optional fixed `<port> <origin>` routes serve clients that can only be pointed at a URL. Token caches are per origin, single-flight, with a 60s login cooldown so a burst of failures cannot stack up SSO tabs; request bodies are buffered so a token retry replays a POST byte-for-byte.
- **Learned gating.** The first request to an origin goes out bare and only a redirect to `cdn-cgi/access/login` marks it gated — so non-gated hosts never trigger an SSO attempt and a newly gated one starts getting tokens on its own, with no configuration.
- **`cf-access-preload.cjs`** — `NODE_OPTIONS=--require` shim patching `http`/`https`/`fetch` to route allowed hosts into the proxy, so an unmodifiable Node client (an MCP server, a vendored SDK) keeps its real URL and needs no code change. Refuses to patch the proxy itself, which would aim it at its own port forever.
- **Suffix allowlist** (`~/.config/cloudflare-access/hosts`) — domains, not apps, so an app added under the domain later is covered for free. It is also the security boundary that stops the dynamic port from being an open forwarder on loopback; a missing file allows nothing rather than defaulting to a domain.
- **`install.sh`** — symlinks the three scripts into a bin dir (default `~/.claude/bin`), seeds the config files from templates without overwriting, writes the launchd plist with the detected `node` plus an explicit `PATH`/`CF_ACCESS_BIN` (launchd starts with a bare environment, and the proxy shells out to `cf-access`), then loads the agent and health-checks the port. `status` reports links, config, `cloudflared`, daemon state, port liveness and per-app token TTL; `uninstall` unloads and unlinks only its own symlinks, keeping config and tokens.
- **SKILL.md** — layer-selection table (per-invocation token vs fixed port vs preload), MCP wiring patterns for both the launcher and preload forms, and a troubleshooting table mapping each originated status code (`511`/`403`/`508`/`400`/`502`) to its cause.

### Security

- Config never carries a token; JWTs are passed by env or header only, and the skill's rules forbid printing one into a transcript, commit or log.
- The proxy binds `127.0.0.1` exclusively, and forwards only to hosts matching the operator's own suffix allowlist.

# session-migration

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
