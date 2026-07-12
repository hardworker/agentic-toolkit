# Changelog

All notable changes to the `adversarial-review` skill.

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
