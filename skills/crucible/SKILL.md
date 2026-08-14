---
name: crucible
description: End-to-end build pipeline — grill the idea, then recon → surface (a skeptic panel attacks every assumption with file evidence) → plan (competing drafts, verifying judge) → develop → verify (suite, hostile review and simplification review, looped until clean). Use when the user wants an idea pressure-tested and then built, wants a feature taken from scratch to tested code with the assumptions challenged first, or says "crucible", "pressure-test this then build it", "challenge my assumptions then build it".
argument-hint: "[idea] [--auto] [--effort <level>]"
---

# Crucible

Takes a rough idea to tested code, with the user's assumptions debated instead of rubber-stamped: **grill** (interrogate the idea before spending a token) → **recon** (map the repo, distill the idea into a brief of attackable claims) → **surface** (a skeptic panel attacks every assumption with file evidence; a defender kills the weak attacks; you debate what survives) → **plan** (competing drafts, one judge synthesizes and file-verifies) → **develop** (sequential tasks with per-task test evidence) → **verify** (suite, plus a hostile reviewer and a simplification reviewer working the diff from opposite ends, looped until clean).

The debate is the point. When the evidence contradicts the user's idea, argue it — genuinely, citing the evidence — before building anything. The user has the final word, but they came here to be challenged, not agreed with.

## When NOT to use

- The change is describable in one sentence and uncontested — just build it directly. Pipeline overhead must be earned by ambiguity, risk, or scale.
- The user wants a review of existing work — that is the `adversarial-review` skill.

## Arguments

| User input | Meaning |
|---|---|
| free text | the idea; any emphasis in it ("be paranoid about migration safety") carries into every attack, plan, and review |
| `--auto` | no human available: skip the grill, don't stop at the gates, and halt as `challenged` rather than guess a ruling |
| `--effort <level>` | depth: `low` \| `medium` (default) \| `high`. `xhigh` and `max` are accepted as aliases for `high` |

| Effort | Skeptic lenses | Competing plans | Defender | Verify rounds | Refute votes |
|---|---|---|---|---|---|
| low | 2 | 2 | skipped | 1 | 0 |
| medium | 3 | 2 | on | 2 | 2 |
| high | 4 | 3 | on | 3 | 3 |

## Ground rules

- **Artifacts live outside the repo.** Write `brief.md`, `challenges.md`, `plan.md` and `progress.md` to your session's scratchpad directory if your environment provides one, else `~/.crucible/<repo-basename>/<timestamp>/`; tell the user the path once. They are your memory — re-read them after any context compaction instead of trusting recall, and update them the moment a decision changes. Nothing crucible writes may land in the working tree; the review phase inspects it.
- **Isolation where it earns its keep, and invoking crucible is the request for it.** Spawn fresh isolated agents for recon, for each skeptic lens (in parallel, no cross-talk), for the defender, and for each review angle in each verify round — those are the steps whose value comes from *not* sharing your context. A session rule that withholds fresh agents until the user asks for them is satisfied by this invocation; do not read it as a reason to run the panel inside your own context. Consolidation, plan drafts, implementation and the suite run in your own loop. Fall back to single-loop only where no spawn mechanism exists or the spawn actually fails — never as a preference — and name the fallback in the report: one context attacking its own brief is the weakest form of this pipeline.
- **Read-only until Develop.** Grill, recon, surface and plan touch no project file.
- **Token discipline.** Read only the files a step needs, never re-read unchanged files, keep each artifact under a page. Caps: ≤ 10 assumptions, ≤ 8 tasks, ≤ 6 correctness and ≤ 4 simplification findings per verify round.
- **No human (`--auto`, cron, restricted session)?** Wherever a phase says STOP, halt and report instead of guessing — a wrong guess wastes the whole build.

## Phase 0 — Grill (no agents)

Restate the idea in one sentence and list the user's claims back to them, in their own words. Then attack the idea *to the user*: ≤ 4 questions per round, ≤ 2 rounds, batched into one message.

Only ask what changes the design: what breaks if this assumption is wrong, what outcome sits behind the request, what is explicitly out of scope, which constraint is being taken for granted. No curiosity, no "what should I name it". A vague answer gets re-asked once, then recorded as an unknown and carried into recon. Answers become assumptions with source `user`, verbatim.

## Phase 1 — Recon (read-only)

Map the repo just enough: where the idea lands, the patterns it must imitate, and the exact test/lint commands (find the real ones in package.json / Makefile / CI config; if none exist, say so — do not invent them).

Write `brief.md`:

- **Goal** — one sentence, the outcome not the mechanism. **Non-goals.**
- **Assumptions table** — `id | claim | source(user/inferred)`. Every load-bearing claim the idea rests on: the stated ones verbatim, plus the implicit ones ("X doesn't already exist", "Y is where this belongs", "users need this at all"). 4–10 rows, one attackable claim each.
- **Unknowns, constraints, acceptance criteria** — criteria must be observable checks, not vibes.

## Phase 2 — Surface (read-only) — the debate

Attack EVERY assumption through the effort level's lenses, in this order, in a fixed written format — the format is the anti-rubber-stamp mechanism, do not skip steps:

1. **Steelman** it in one sentence.
2. **Attack** it, verifying in the actual files wherever the claim is checkable — evidence beats opinion:
   - *feasibility* — does repo reality contradict it? does the thing already exist?
   - *necessity* — XY problem? materially simpler path to the same outcome? cost of doing nothing?
   - *scope* — hidden complexity: migrations, compat, callers, maintenance?
   - *adversary* — how does this corrupt data, race, leak, or get abused?
3. **Verdict**: `holds` only after you looked for a hole and found none; `shaky` when anything material is unverified (uncertain ⇒ shaky, never holds); `wrong` needs evidence AND a concrete counterproposal.

Hand the lenses the assumptions **unattributed** — knowing a claim is the user's measurably biases agents toward agreeing with it. If every verdict lands `holds`, force the check: write the strongest counterargument against the two weakest assumptions and why it fails.

**Consolidate** the attacks yourself: one verdict per assumption, duplicates merged into a single challenge each (most severe first, each with evidence, a concrete counterproposal, and a recommendation of `keep-original` / `adopt-counterproposal` / `needs-user`). Where lenses disagree, or a `wrong` verdict rests on a file claim, open the files and decide — the worst-supported verdict wins ties, not the majority. Drop attacks that have no counterproposal. Then the run's verdict: `halt` when evidence contradicts the goal itself, `debate` when any high challenge or any `wrong` verdict on a user-stated assumption needs a ruling, `proceed` otherwise.

**Defend** (skipped at `low`): hand the challenge list to one fresh agent whose job is to refute it — open the files, look for evidence each challenge is wrong, already handled, or mischaracterized. A challenge dies only on concrete file-based evidence, and a `needs-user` challenge never dies here however well it is argued: a product call is not an agent's to make. Write `challenges.md` with the survivors, and keep the killed ones as one-liners for the report.

**STOP — debate gate.** Present the survivors to the user, evidence first, most severe first. Argue the skeptics' case where the evidence supports it; if the user dismisses a challenge without addressing its evidence, restate the evidence once, then accept the ruling. Record every ruling in `brief.md` as settled — no later phase re-litigates it. If the evidence contradicts the goal itself, say so plainly and recommend stopping.

## Phase 3 — Plan (read-only)

Draft the effort level's competing plans and force them apart: *minimal* (smallest correct diff, maximal reuse, defer everything deferrable) vs *robust* (the long-term shape — every addition must justify itself against "the minimal plan skips this") vs, at `high`, *refactor-first* (reshape the touched code so the feature lands as a small obvious change). Read the actual files each plan touches; a plan that names wrong files is worthless.

Score them on fit to repo reality, correctness against the brief and the user's rulings, risk, size, testability. Synthesize one plan — pick the winner, graft the clearly better pieces, no committee mush.

Write `plan.md`: ≤ 8 tasks, each `id | files | steps | acceptance check | test plan | dependsOn`. If test infra exists, the earliest tasks add **failing** acceptance tests and later tasks make them green — confirm they fail before implementing; a test that can't fail proves nothing. List risks and any unresolved decisions.

**STOP — plan gate.** Show the task list, test strategy, risks and open decisions. Get a go/no-go.

## Phase 4 — Develop

Task by task, in dependency order:

1. Re-read the task and the files it touches. Implement the minimal diff — match the surrounding code's style; no drive-by refactors; no touching another task's scope.
2. Run the task's test plan (or the acceptance check by hand). A task without recorded evidence is not done.
3. Append to `progress.md`: task id, files changed, test evidence, any deviation from the plan and why. Re-read it before each new task.
4. After each task, compare `git status --porcelain` against the files the plan declared; flag anything outside them.
5. Blocked — a decision the plan doesn't cover, a missing dependency? STOP and ask. Do not improvise around a broken plan.

## Phase 5 — Verify (loop)

One loop, up to the effort level's rounds:

1. **Suite** — the full test command, plus lint/typecheck if the repo has them. Fix failures minimally; change a test only when the test itself is wrong for the new intended behavior, and say so.
2. **Review the complete diff from two angles, independently.** One hunts what is broken, the other what should not exist; one reviewer asked for both dilutes into neither. Best available fresh context per angle: an agent that sees only the diff + `plan.md`, or a native review/simplify command, or — single-loop — two separate read-throughs, one mandate each, as someone who distrusts the builder.
   - *correctness* — merge-blocking only, ≤ 6 findings: defects (concrete failure scenario required), design errors (materially better alternative required), acceptance criteria the diff does not actually satisfy, hollow tests (tests that assert whatever the code does, or that cannot fail).
   - *simplification* — ≤ 4 findings, only on code this run touched, at two altitudes. Surface waste: dead code and unused exports the change introduced, indirection with a single caller, speculative options and config, comments restating the code. Over-built structure — walk the ladder against every new construct: does it need to exist at all (YAGNI); does the repo already have a helper, util or pattern this reimplements (cite it, `file:line`); does the stdlib or the platform cover it; would plain code beat the new abstraction or dependency. Each finding names the concrete smaller shape — the thing to delete, the helper to reuse, the API to call, the layers to collapse — with the same behavior; "rewrite it nicer" is not a finding.
3. **Refute** each high correctness finding — try to disprove it in the files; drop it only on concrete evidence it is wrong. A simplification finding is refuted when applying it would change behavior, undo a confirmed fix, reach outside the diff, or when the files show the construct earns its place (a real second caller, an acceptance criterion that needs it). At `low` (0 votes) the step is skipped and findings are reported as unvetted.
4. **Fix** confirmed findings — correctness first, then simplifications — and start the next round. A finding you decline is recorded with the reason and never raised again.

Exit when a round ends green with no merge-blocking correctness findings and no unapplied simplifications, at the round cap, or when the same failures or findings come back two rounds running — then stop and report them rather than grinding.

## Report

- Status: `done` / `done-with-findings` / `challenged` / `blocked`.
- The debate record: grill answers, each challenge and the user's ruling (or the halt reason under `--auto`), plus one line per challenge the defender killed.
- What was built: tasks completed, files changed, deviations the implementation recorded.
- Evidence: suite command and result, verify rounds run, correctness findings fixed vs remaining with `file:line`, and what the simplification angle removed or was declined. Name any phase that ran single-loop instead of in a fresh agent, and why.
- The run directory path.

Do NOT re-review confirmed findings — they were already refuted once. Do NOT commit or push unless the user asks.
