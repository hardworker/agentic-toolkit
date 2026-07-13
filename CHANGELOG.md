# Changelog

All notable changes to the `adversarial-review` skill.

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
