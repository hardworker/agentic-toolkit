---
name: adversarial-review
description: Adversarial Claude-vs-Codex debate review of any target — a branch diff, the working tree, or documents (specs, proposals, plans). Hunts real defects AND challenges design decisions, approaches, and implementation paths. Use when the user asks for an adversarial review, debate review, cross-model review, or hostile scrutiny of code or plans.
argument-hint: "[path | working-tree] [--base <ref>] [--fix] [--iterations <n>] [--effort <level>] [--strict] [--no-codex] [--cwd <path>] [focus text]"
---

# Adversarial Review

Run the adversarial-review Workflow and report its verdict. The debate: independent Claude + Codex reviews → cross-examination → synthesis judge that verifies disputes in the actual files → optional fix loop.

## Invoke

Call the **Workflow tool** with:
- `scriptPath`: the `adversarial-review.mjs` file in this skill's directory (the same directory as this SKILL.md).
- `args`: object assembled from the user's arguments (all optional):

| User input | JSON arg | Meaning |
|---|---|---|
| _(nothing)_ | `target: "auto"` | uncommitted changes if any, else branch diff vs default branch |
| `working-tree` | `target: "working-tree"` | uncommitted changes only |
| `--base <ref>` (or a bare git ref) | `target: "<ref>"` | branch diff vs merge-base with `<ref>` |
| a directory or file path | `target: "<path>"` | review those files as they stand — code or documents (e.g. `openspec/changes/<name>/`) |
| `--fix` | `fix: true` | debate → apply confirmed fixes → re-review, up to `maxIterations` (default 3) |
| `--iterations <n>` | `maxIterations: n` | fix-loop cap |
| `--strict` | `strict: true` | low-noise mode: only merge-blocking findings survive, ≤5 issues/reviewer |
| `--no-codex` | `codex: false` | skip the Codex leg (cheaper; a fresh Claude critic still cross-examines) |
| `--effort <level>` | `effort: "<level>"` | review depth, same scale as /code-review: `low` \| `medium` (default) \| `high` \| `xhigh` \| `max`. low = few merge-blocking findings, cheap agents, no refute panel; medium = the standard pipeline; high and above = wider net (reviewers also raise suspicions for the debate to filter), bigger issue caps, stronger reasoning tiers, 3-vote panel at xhigh+ |
| `--cwd <path>` (or when reviewing another repo's checkout; legacy `--repo`) | `cwd: "<absolute root>"` | review a repo outside the session cwd; checkout/worktree must already be at the right commit |
| remaining free text | `focus: "<text>"` | extra lens for the reviewers (e.g. "these are OpenSpec artifacts; check tasks cover the specs") |

Bare legacy keywords (`fix`, `solo`, `iterations <n>`, `base <ref>`) mean the same as their flags; `solo` ≡ `--no-codex`.

Runs in the background (~15–35 min; ~300k subagent tokens per iteration for small/clean diffs, up to ~650k for a large PR with a heavy debate — noticeably less at `--effort low`, more at `high` and above). Don't block on it if the user has more requests.

## Report

When it completes, report:
- Status (`clean` / `issues-found` / `stagnant` / `max-iterations` / `scope-violation`), iterations run; if `codexAvailable` is false, note the debate ran single-model (Codex CLI down or unauthenticated; `codex login` restores it). `scope-violation` = the fixer touched files no finding names; the run stopped so the user can inspect the working tree.
- Each confirmed finding: kind (`defect`/`design`), severity, `file:line`, title, impact, agreement (`both`/`claude-only`/`codex-only`), fixRecommendation.
- Fix mode: fixed vs. remaining unfixed.

Do NOT re-review or second-guess the findings — the debate already cross-verified them. Do NOT apply fixes in report-only mode unless the user then asks.
