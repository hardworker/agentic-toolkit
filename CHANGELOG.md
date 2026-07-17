# Changelog

Per-skill changelogs; each skill follows Keep a Changelog / SemVer independently.

# crucible

## [1.0.0] — 2026-07-16

Initial release: end-to-end build pipeline (idea → tested code) that debates the user's assumptions before building. Designed from a survey of the 2024–2026 multi-agent literature (Debate-or-Vote, Cost-of-Consensus, SycEval, MAST, Cognition/Anthropic orchestration guidance, SWE-bench ensembling analyses); the load-bearing citations live in ARCHITECTURE.md.

### Added

- **Phase-parameterized Workflow script** (`crucible.mjs`) — `phase: surface | plan | develop | test | full`; the main thread chains invocations with a debate gate after surface and a go/no-go gate after plan; `full` is the autonomous mode that halts (`challenged`) instead of guessing whenever a human ruling is needed; `--dry` (`dry: true`) is a write-guard: the thinking phases run, develop is skipped (a build run ends after planning as `planned`), and test-phase fixes are disabled — findings get reported, never applied.
- **Skeptic panel (surface phase)** — 2–4 isolated lenses (feasibility / necessity / scope / adversary) attack every brief assumption with file evidence; no cross-talk between skeptics; assumptions passed unattributed (naming the user's position measurably increases agreement with it); uncertainty maps to `shaky`, never `holds`; a consolidating judge file-verifies contested verdicts.
- **Competing plans + verifying judge (plan phase)** — 2–3 forced-apart planner angles (minimal / robust / refactor-first); the judge spot-checks file claims by opening files, synthesizes one plan of ≤ 8 tasks, keeps test-first ordering when test infra exists, and surfaces `planChallenges` for genuine product calls.
- **Sequential develop phase** — one implementer agent per task in dependency order, each seeing the whole plan, completed-task summaries, and deviations; per-task test evidence required; `blocked` stops the run instead of improvising; out-of-plan file touches are logged.
- **Test + hostile review phase** — full suite with a bounded fix loop (stagnation fingerprint breaker), fresh-context reviewer hunting merge-blocking defects/design/acceptance-gaps/hollow-tests, 2-vote refute panel on high findings, auto-fix of confirmed high/medium findings with one suite re-run.
- **Budget as a first-class mechanism** — fan-outs scale to the workflow token budget (reserve-half rule, ~70k/agent from sibling field data), every phase boundary stops cleanly as `budget-exhausted`, and the result reports actual per-phase spend (`result.tokens`).
- **Sequential fallback (`PLAYBOOK.md`)** — the same pipeline as a portable single-loop protocol per the Agent Skills open standard: no tool names, capability-conditional wording, `.crucible/` phase artifacts as compaction-proof memory. Codex CLI picks it up from `.agents/skills/`; `codex review` slots in as the fresh-eyes reviewer.
- **Stub-runtime smoke test (`eval/crucible-smoke.mjs`)** — executes the real script's control flow with canned agent responses (35 checks: chaining, gates, dry-run write-gating, blocked tasks, stagnation, refute kills, budget floors, error surfacing) at zero token cost.

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
