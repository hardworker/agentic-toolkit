---
name: adversarial-review
description: Adversarial Claude-vs-Codex debate review of any target — a branch diff, the working tree, or documents (specs, proposals, plans). Hunts real defects AND challenges design decisions, approaches, and implementation paths. Use when the user asks for an adversarial review, debate review, cross-model review, or hostile scrutiny of code or plans.
---

# Adversarial Review

Run the adversarial-review Workflow and report its verdict. The debate: independent Claude + Codex reviews → cross-examination → synthesis judge that verifies disputes in the actual files → optional fix loop.

## Invoke

Call the **Workflow tool** with:
- `scriptPath`: the `adversarial-review.mjs` file in this skill's directory (the same directory as this SKILL.md).
- `args`: object assembled from the user's free-form arguments (all optional):

| User says | Arg |
|---|---|
| _(nothing)_ | `target: "auto"` — uncommitted changes if any, else branch diff vs default branch |
| `working-tree` | `target: "working-tree"` (uncommitted only) |
| `base <ref>` / a git ref | `target: "<ref>"` (branch diff vs merge-base) |
| a directory or file path(s) | `target: "<path>"` — reviews those files as they stand (code or documents, e.g. `openspec/changes/<name>/`) |
| `fix` | `fix: true` (debate → apply confirmed fixes → re-review, up to `maxIterations`, default 3) |
| `iterations <n>` | `maxIterations: n` |
| `solo` | `solo: true` (skip the Codex leg — cheaper, single-model) |
| a repo outside the cwd (e.g. reviewing a PR of another repo) | `repo: "<absolute path to its root>"` — checkout/worktree must already be at the right commit |
| remaining free text | `focus: "<text>"` — extra lens for the reviewers (e.g. "these are OpenSpec artifacts; check tasks cover the specs") |

Runs in the background (~15–35 min; ~300k subagent tokens per iteration for small/clean diffs, up to ~650k for a large PR with a heavy debate). Don't block on it if the user has more requests.

## Report

When it completes, report:
- Status (`clean` / `issues-found` / `stagnant` / `max-iterations`), iterations run; if `codexAvailable` is false, note the debate ran single-model (Codex CLI down or unauthenticated; `codex login` restores it).
- Each confirmed finding: kind (`defect`/`design`), severity, `file:line`, title, agreement (`both`/`claude-only`/`codex-only`), fixRecommendation.
- Fix mode: fixed vs. remaining unfixed.

Do NOT re-review or second-guess the findings — the debate already cross-verified them. Do NOT apply fixes in report-only mode unless the user then asks.
