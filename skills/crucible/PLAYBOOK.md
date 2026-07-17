# Crucible — sequential playbook

The crucible pipeline for environments without a workflow orchestrator: same five phases, same gates, run sequentially in one agent loop. Written tool-agnostically — it works in Codex CLI, Claude Code without the Workflow tool, or any agent that can read files, edit files, and run shell commands.

**Ground rules for the whole run:**

- Persist every phase artifact to `.crucible/` in the repo root (`brief.md`, `challenges.md`, `plan.md`, `progress.md`). These files are your memory: re-read them after any context compaction instead of trusting recall, and update them the moment a decision changes. Keep `.crucible/` out of commits: add it to `.git/info/exclude` (never to `.gitignore` — that would dirty the working tree the review phase inspects).
- Do not modify any project file before the Develop phase. Recon, Surface, and Plan are read-only (add `.crucible/` writes only).
- Token discipline: read only the files a step needs, never re-read unchanged files, keep each artifact under one page. Caps: ≤ 10 assumptions, ≤ 8 tasks, ≤ 6 review findings.
- Non-interactive run (no user available): wherever a phase says STOP, halt and report instead of guessing — a wrong guess wastes the whole build.
- Flags map here too: `--effort low` → attack through the first two lenses only, two competing plans, 1 fix round in Phase 5, skip the refute step; `medium` (default) → this playbook as written; `high` and above → all four lenses, three competing plans (add *refactor-first*: prepare the code so the feature lands as a small change), 3 fix rounds. `--auto` → the non-interactive rule above; `--focus <text>` → carry the emphasis into every attack, plan, and review step. A plan-only request simply ends at the Phase 3 gate.

## Phase 1 — Recon (read-only)

If the idea is too vague to attack (no target, no outcome), ask the user up to 3 clarifying questions before anything else — every phase downstream is wasted on a vague brief.

Map the repo just enough: where the idea lands, the patterns it must imitate, and the exact test/lint commands (find the real ones in package.json / Makefile / CI config; if none exist, say so — do not invent them).

Write `.crucible/brief.md`:

- **Goal** — one sentence, the outcome not the mechanism. **Non-goals.**
- **Assumptions table** — `id | claim | source(user/inferred)`. Every load-bearing claim the idea rests on, stated ones verbatim plus the implicit ones ("X doesn't already exist", "Y is where this belongs", "users need this at all"). 4–10 rows, one attackable claim each.
- **Unknowns, constraints, acceptance criteria** — criteria must be observable checks, not vibes.

## Phase 2 — Surface (read-only) — the debate

For EVERY assumption, in a fixed written format (the format is the anti-rubber-stamp mechanism — do not skip steps):

1. **Steelman** it in one sentence.
2. **Attack** it through four lenses, verifying in the actual files wherever the claim is checkable — evidence beats opinion:
   - *feasibility* — does repo reality contradict it? does the thing already exist?
   - *necessity* — XY problem? materially simpler path to the same outcome? cost of doing nothing?
   - *scope* — hidden complexity: migrations, compat, callers, maintenance?
   - *adversary* — how does this corrupt data, race, leak, or get abused?
3. **Verdict**: `holds` only after you looked for a hole and found none; `shaky` when anything material is unverified (uncertain ⇒ shaky, never holds); `wrong` needs evidence AND a concrete counterproposal.

Treat the assumptions as unattributed claims while attacking — ignore who stated them; knowing a claim is the user's measurably biases agents toward agreeing with it. If every verdict lands `holds`, force the check: write the strongest counterargument against the two weakest assumptions and why it fails. If your environment can spawn fresh isolated agents, give each lens to one (assumptions unattributed) and consolidate their verdicts yourself.

Write `.crucible/challenges.md`: verdict per assumption, challenges (most severe first, each with evidence + counterproposal + a recommendation of `keep-original` / `adopt-counterproposal` / `needs-user`), open questions.

**STOP — debate gate.** Present the challenges to the user, evidence first, most severe first. Argue the skeptics' case where the evidence supports it; if the user dismisses a challenge without addressing its evidence, restate the evidence once, then accept the ruling. Record every ruling in `brief.md` as settled — do not re-litigate later. If the evidence contradicts the goal itself (it already exists, the premise is false), say so plainly and recommend stopping.

## Phase 3 — Plan (read-only)

Draft **two competing plans** and force them apart: *minimal* (smallest correct diff, maximal reuse, defer everything deferrable) vs *robust* (the long-term shape — but every addition must justify itself against "the minimal plan skips this"). Read the actual files each plan touches; a plan that names wrong files is worthless.

Score both against: fit to repo reality, correctness vs the brief and the user's rulings, risk, size, testability. Synthesize one plan — pick the winner, graft clearly-better pieces, no committee mush.

Write `.crucible/plan.md`: ≤ 8 tasks, each with `id | files | steps | acceptance check | test plan | dependsOn`. If test infra exists, the earliest tasks add **failing** acceptance tests and later tasks make them green (confirm the tests fail before implementing — a test that can't fail proves nothing). List risks and any unresolved decisions.

**STOP — plan gate.** Show the task list, test strategy, risks, and open decisions. Get a go/no-go.

## Phase 4 — Develop

Task by task, in dependency order:

1. Re-read the task and the files it touches. Implement the minimal diff for the task — match the surrounding code's style; no drive-by refactors; no touching other tasks' scope.
2. Run the task's test plan (or the acceptance check by hand). A task without recorded evidence is not done.
3. Append to `.crucible/progress.md`: task id, what changed (files), test evidence, any deviation from the plan and why. Re-read `progress.md` before each new task — it is the coordination record.
4. Blocked (a decision the plan doesn't cover, a missing dependency)? STOP and ask — do not improvise around a broken plan.

## Phase 5 — Test + hostile review

1. **Full suite** (plus lint/typecheck if the repo has them). Fix failures minimally — change a test only when the test itself is wrong for the new intended behavior, and say so. Max 2 fix rounds; if the same failures survive two rounds, stop and report them.
2. **Fresh-eyes review** of the complete diff. Best available fresh context first: a spawned agent that sees only the diff + `plan.md`, or a native review command (e.g. `codex review`), or a second model. Single-loop fallback: re-read the full diff file-by-file as a hostile reviewer who distrusts the builder. Hunt only merge-blocking findings (≤ 6): defects (concrete failure scenario required), design errors (materially better alternative required), acceptance criteria the diff doesn't actually satisfy, and hollow tests (tests that assert whatever the code does, or that cannot fail).
3. **Refute before reporting**: for each high finding, actively try to disprove it in the files; drop it only with concrete evidence it's wrong.
4. Fix confirmed high/medium findings, re-run the suite once.

## Report

Status (`done` / `done-with-findings` / `challenged` / `blocked` / `test-failures`); the debate record (challenges + rulings); tasks completed, files changed, deviations; suite command + result; findings fixed vs remaining with `file:line`. Then delete `.crucible/` (it is excluded from git via `.git/info/exclude`, never committed).
