---
name: crucible
description: End-to-end build pipeline — recon → surface (a skeptic panel attacks the idea's assumptions with file evidence) → plan (competing drafts, verifying judge) → develop → test + hostile review. Use when the user wants an idea pressure-tested and then built, wants a feature taken from scratch to tested code with the assumptions challenged first, or says "crucible", "pressure-test this then build it", "challenge my assumptions then build it".
argument-hint: "[idea] [--auto] [--dry] [--thorough] [--focus <text>] [--cwd <path>] [--phase <surface|plan|develop|test>]"
---

# Crucible

Takes a rough idea to tested code through five phases, with the user's assumptions debated instead of rubber-stamped: **recon** (map the repo, distill the idea into a brief with explicit assumptions) → **surface** (a skeptic panel attacks every assumption with file evidence; you then debate the survivors with the user) → **plan** (competing drafts from different angles, one judge synthesizes and file-verifies) → **develop** (sequential task implementation with per-task test evidence) → **test** (full suite, bounded fix loop, fresh-eyes hostile review with refute votes).

The debate is the point. When the skeptics' evidence contradicts the user's idea, argue it — genuinely, citing the evidence — before building anything. The user has the final word, but they came here to be challenged, not agreed with.

## When NOT to use

- The change is describable in one sentence and uncontested — just build it directly. Pipeline overhead must be earned by ambiguity, risk, or scale.
- The user wants a review of existing work — that is the `adversarial-review` skill.

## Arguments

| User input | Meaning |
|---|---|
| free text | the idea (first run) — pass verbatim as `idea` |
| `--auto` | one-shot `phase: "full"` run, no user gates; halts as `challenged` instead of guessing when a ruling is needed |
| `--thorough` | max panel sizes (4 skeptics, 3 planners, 3 test-fix rounds) |
| `--dry` | write-guard, `dry: true`: never modify project files — develop is skipped (a build run ends after planning as `planned`), and a `--dry --phase test` run reports suite failures and review findings instead of fixing them |
| `--focus <text>` | extra emphasis for skeptics, planners, and reviewer beyond the idea itself (e.g. "be paranoid about migration safety") |
| `--cwd <path>` | working directory: absolute repo root when it is not the session cwd |
| `--phase <name>` | run a single phase (needs that phase's inputs from a prior run) |

Flag→arg mapping is Path A semantics; Path B reads the same flags per its ground rules.

## Intake — both paths, before any tokens are spent

Restate the idea in one sentence and list the user's claims that will become assumptions — quote their own words. If the idea is too vague to attack (no target, no outcome), ask up to 3 clarifying questions FIRST; every phase downstream is wasted on a vague brief.

## Path A — orchestrated (requires the Workflow tool)

If the Workflow tool is available (Claude Code), run phases as separate Workflow invocations with `scriptPath` = the `crucible.mjs` next to this SKILL.md, gating between them. Runs happen in the background — don't block on them if the user has other requests. If the user's message carries a token target (e.g. "+500k"), the workflow's budget picks it up and the panels scale to it automatically.

**1. Surface.** `args: { phase: "surface", idea: "<verbatim>", assumptions: ["<user's stated claims>"], focus?, cwd?, thorough? }` → returns `{ brief, repoMap, surface }`.

**2. Debate gate (the core of this skill).** Present `surface.challenges` to the user, most severe first: title, the evidence, the counterproposal, the panel's recommendation. Conduct rules:
- Lead with the evidence, not with deference. If the panel found `src/x.js` already does the thing, open with that.
- Argue the skeptics' case where the evidence supports it. If the user dismisses a challenge without addressing its evidence, restate the evidence once — then accept their ruling.
- Ask the user to rule on each `needs-user` challenge (AskUserQuestion works well, ≤4 at a time; recommended option first).
- Record rulings as `resolutions: [{ id, decision: "keep-original" | "adopt-counterproposal" | "revise", note }]`. Rulings are settled — later phases must not re-litigate them.
- `surface.proceed === "halt"` means the evidence contradicts the goal itself (e.g. it already exists). Say so plainly and stop unless the user overrules.

**3. Plan.** `args: { phase: "plan", brief, repoMap, resolutions, focus?, cwd?, thorough? }` (edit `brief` first if rulings changed the goal) → returns `{ plan }`. Show the user: task list (title + files), test strategy, risks, and every `planChallenge` — get a go/no-go. With `--dry`, this is where a build run ends (develop is write-gated): report the brief, the debate record, and the plan — no code gets written.

**4. Build.** `args: { phase: "develop", plan, repoMap, brief?, cwd? }` → returns `{ taskResults, changedFiles }`; pass both verbatim into the next invocation, immediately and with no gate: `args: { phase: "test", plan, brief, repoMap, taskResults, changedFiles, cwd? }`. A `blocked` status means a task hit a decision the plan didn't cover — bring the `blockedReason` to the user, don't improvise.

**5. Report** (see below). Optionally offer `/adversarial-review --strict` as an extra cross-model gate on the final diff, and a commit.

`--auto`: single invocation `args: { phase: "full", idea, assumptions, ... }`. It halts (`challenged`) rather than guessing whenever a human ruling is needed. After a halt: settle the rulings with the user, then resume with per-phase invocations from where it stopped — `phase: "plan"` with the returned `brief`/`repoMap` plus `resolutions` after a surface halt; `phase: "develop"` with the returned `plan` after a plan halt. `--auto --dry` (`dry: true`) runs the same invocation but skips the build: status `planned` after planning.

Cost expectations (estimates from this repo's per-agent field data, ~50–80k tokens/agent): surface ≈ 4–6 agents, plan ≈ 3–4, develop ≈ 1 per task (≤8), test ≈ 2–10+ (refute votes scale with high findings). A small feature end-to-end ≈ 0.8–1.5M subagent tokens. The script reports actual per-phase spend in `result.tokens`.

## Path B — sequential fallback (no Workflow tool)

In any environment without the Workflow tool — Codex CLI, restricted sessions, any Agent-Skills-compatible agent — follow **PLAYBOOK.md** in this skill's directory: the same five phases and gates run sequentially in one context, with phase artifacts persisted to `.crucible/` files. If your environment can spawn fresh isolated agents, the playbook says where they help (skeptic lenses, fresh-eyes review); otherwise every step works single-loop.

## Report

When the run completes, report:
- Status: `done` / `done-with-findings` / `planned` (dry run) / `challenged` / `blocked` / `test-failures` / `budget-exhausted` / `agent-failed` / `error`. (Standalone surface/plan/develop invocations return `ok` — those are phase completions, not build verdicts.)
- The debate record: each challenge, the user's ruling (or the halt reason in `--auto`).
- What was built: tasks completed, files changed, deviations the implementers recorded.
- Evidence: suite command + result, review findings fixed vs remaining (with `file:line`).
- Per-phase token spend from `result.tokens`.

Do NOT re-review or second-guess confirmed findings — the refute panel already vetted them. Do NOT commit or push unless the user asks.
