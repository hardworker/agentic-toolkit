---
name: adversarial-review
description: Adversarial Claude-vs-Codex debate review of any target — a branch diff, the working tree, or documents (specs, proposals, plans). Hunts real defects AND challenges design decisions, approaches, and implementation paths. Use when the user asks for an adversarial review, debate review, cross-model review, or hostile scrutiny of code or plans.
argument-hint: "[path | working-tree | git ref] [--fix] [--effort low|medium|high] [--no-codex] [focus text]"
---

# Adversarial Review

Two independent reviewers — a fresh agent and the Codex CLI — review the same target, then argue about their findings until they either agree or deadlock. A fresh judge verifies what is left in the actual files before anything reaches the user.

**Your role is orchestrator.** You route the debate and report. You never read the target yourself, never take a side, and never re-litigate the judge's verdict — you own the bookkeeping (whose finding is whose, what is still disputed, when a round changed nothing), and nothing else.

This runs long: 4 subagents and 2 Codex calls minimum, plus 2 calls per extra debate round and 1 agent with `--fix`. Say the review is running; don't block on it if the user has more requests.

Agent spawns below name Claude Code's `general-purpose` subagent type and Claude model names; on another runtime, substitute its own fresh-agent mechanism and model tiers. A runtime that cannot spawn fresh agents cannot run this pipeline — every role depends on starting cold, so a session rule that withholds fresh agents until the user asks for them is satisfied by this invocation. If the spawn mechanism is genuinely absent, report `error` rather than reviewing the target yourself.

## Arguments

| User input | Setting | Meaning |
|---|---|---|
| _(nothing)_ | `target = auto` | uncommitted changes if any, else branch diff vs the default branch |
| `working-tree` | `target = working-tree` | uncommitted changes only |
| a git ref | `target = <ref>` | branch diff vs merge-base with `<ref>` |
| a directory or file paths | `target = <paths>` | review those files as they stand — code or documents (e.g. `openspec/changes/<name>/`) |
| `--fix` | fix loop on | debate → apply confirmed fixes → re-review, max 3 iterations |
| `--no-codex` | solo | skip the Codex leg; a fresh critic still cross-examines |
| `--effort <level>` | `effort = <level>` | `low` \| `medium` (default) \| `high` — see below |
| remaining free text | `focus` | extra lens for the reviewers (e.g. "these are OpenSpec artifacts; check tasks cover the specs") |

The debate is capped at 3 rounds; both caps are backstops — each loop stops earlier the moment it agrees or stops moving.

### Effort presets

| level | issues/reviewer | finding bar | reviewer & critic model | judge model |
|---|---|---|---|---|
| `low` | 5 | strict — merge-blocking only | `sonnet` | inherit |
| `medium` | 10 | standard | inherit | `opus` |
| `high` | 20 | wide net | `opus` | `opus` |

"inherit" = omit the model so the agent runs on the session model. `xhigh` and `max` are accepted and mean `high`.

## Step 1 — Scope

Spawn one `general-purpose` agent, model `sonnet`. It resolves the target and nothing else — the diff must never enter your context, and it is not a rule you can follow by being careful, so a separate context holds it.

> You resolve the scope of a review. Do NOT review anything yourself and do not judge what you see.
> Target spec: "`<target>`". Resolve it:
> - `auto`: run `git status --porcelain`; if there are uncommitted changes treat as `working-tree`, else diff HEAD against the repo default branch (treat as a ref target).
> - `working-tree`: UNCOMMITTED changes only. files = changed and untracked paths. diffCommand = `git diff HEAD && git status --porcelain`, plus a note that untracked files must be read directly. Do NOT widen the scope to the branch diff even if the uncommitted delta is tiny.
> - a git ref: run `git merge-base <ref> HEAD`; files from `git diff --name-status <mb>...HEAD`; diffCommand = `git diff <mb>...HEAD`. If the ref does not exist, fall back to the repo default branch and say so in the summary.
> - a path or several: files = those files (list a directory recursively; skip binaries and scaffolding like `.openspec.yaml`). No diffCommand — they are reviewed as they stand, and may be code or documents.
>
> Read enough of the change to say what it is about; you may read the diff, but report no opinion on it.
> Return ONLY JSON: `{"empty": bool, "files": ["paths"], "summary": "one paragraph on what is under review", "diffCommand": "the exact command reviewers run, omitted when reviewing files as they stand"}`

`empty` or no files → report `nothing-to-review` and stop.

### The context block

Step 1 produces the preamble every stage prompt starts with, the fixer included. Assemble it once and paste it into all of them:

> Target: `<the one-paragraph summary>`
> [diff target: Changed files: `<list>`]
> [diff target: See the changes: run `<diffCommand>`]
> [path target: Files under review (read every one): `<list>`]

Say what you're reviewing, then start the legs.

## Stage answers

Every stage returns JSON and nothing else. Findings:

```jsonc
{ "id": "<prefix>-<n>", "kind": "defect | design", "file": "path", "line": 42,
  "severity": "high | medium | low", "title": "...",
  "description": "max 3 sentences, and say who or what it affects. defect: concrete failure scenario (input/state -> wrong outcome). design: the concrete better alternative and why it is materially better" }
```

Review stage returns `{ "issues": [...], "summary": "..." }`.

Substitute `<values>`; emit `[condition: text]` text only when the condition holds, never the brackets. Prompts can't see this file — paste the JSON shapes in literally. An answer that isn't parseable JSON: ask that same agent to re-emit the JSON only — never re-run the stage, never repair it yourself. Still malformed → report `error`, naming the stage.

## Step 2 — Independent reviews (concurrent)

Both legs get the identical brief, differing only in id prefix. Neither sees the other's output.

**The review brief:**

> You are one of two independent adversarial reviewers. The other works separately; you will cross-examine each other later, so only report findings you can defend.
> `<the context block>`
> [when focus: Focus: `<focus>`]
> [iteration 2+: Already confirmed and fixed by earlier passes — do NOT re-report these unless the fix itself is broken; hunt what was missed instead: `<[{file,title}] JSON>`]
>
> Rules:
> - Read the changes AND enough surrounding code/context to judge. Never judge from a diff alone. For documents, check claims against the actual codebase.
> - [diff targets] Flag ONLY issues these changes introduce or materially worsen. Anything that might pre-date the change: check the merge-base version first, and stay silent if it was already there.
> - Hunt TWO kinds of issue:
>   * **defect** — broken behavior: bugs, broken edge cases, races, security, data loss, API misuse; in documents: contradictions, ambiguity an implementer cannot resolve, missing failure behavior, tasks/specs that do not cover the stated intent. Description = concrete failure scenario: input/state -> wrong outcome.
>   * **design** — the decision itself is wrong: needless complexity, wrong abstraction, fights existing codebase patterns, unnecessary dependency, reinvented standard solution, a path that will bite later. Actively challenge the author's decisions — assume every major choice (data flow, abstraction, dependency, algorithm, API shape) is wrong until it survives scrutiny. Description = the concrete better alternative and why it is materially better here.
> - No style nits, no praise, no "could be nicer" without a defensible alternative.
> - Severity is anchored to merge impact: high = a maintainer would block the merge (wrong behavior/data/security, or a decision locking in real damage); medium = real defect worth fixing, limited blast radius; low = genuine but minor.
> - [effort low] STRICT: report ONLY findings a maintainer would block the merge over. When unsure a finding clears that bar, drop it.
> - [effort high] WIDE NET: also raise findings you suspect but could not fully verify — the cross-examination will filter them. Say plainly in the description what is verified and what is suspicion.
> - At most `<cap>` issues, most important first, description max 3 sentences each. Ids `<prefix>-<n>`.
> - Return ONLY the review JSON, nothing else: `<the finding format and review shape, pasted in>`

**2a — Claude leg.** Spawn one `general-purpose` agent with the brief, prefix `claude`, model per the effort table. Background it.

**2b — Codex leg** (skip when `--no-codex`). While the Claude agent runs, do it yourself:

1. Write the brief (prefix `codex`) to a temp file, and the stage's JSON schema to a second one.
2. Run with a 600000 ms Bash timeout:
   `codex exec --sandbox read-only --output-schema <schema> -o <answer.json> - < <brief> >/tmp/codex-log 2>&1`
3. Read `<answer.json>` — Codex's answer, and the only part you read. The redirect keeps its reasoning transcript out of your context; the log is for the failure path.
4. On any failure, retry **once** adding `--disable code_mode_host` (the Homebrew cask ships without `codex-code-mode-host`).
5. Missing binary, unauthenticated, non-zero exit, unparseable answer, or timeout → read the log, note the exact error, mark Codex unavailable for the rest of the run, and continue single-model. Never substitute your own review for Codex's.

Codex's findings pass on **verbatim** — nothing added, dropped, softened or verified by you.

Wait for both legs before Step 3. Both empty → `clean`, report, done.

## Step 3 — The debate

Each side attacks the other's findings, and the disagreements go back for another round until they resolve. Both sides run concurrently every round: spawn the Claude leg first and background it, then run the Codex leg while it works, exactly as in 2b. Skip a side with nothing to say.

**Round 1 — cross-examination.** Each side verdicts the other's findings:

> You are cross-examining reviewer "`<other>`" in an adversarial review. Be skeptical BOTH ways: hallucinated findings must die, real ones must survive.
> `<the context block>`
>
> `<other>`'s findings: `<JSON>`
>
> For EACH issue id, verify against the actual files — open them; never judge on plausibility.
> - `valid`: real as described
> - `invalid`: hallucinated, already handled, pre-existing rather than introduced by the change under review, or mischaracterized — say exactly why, cite file:line. A design issue is invalid if its alternative is not materially better or not feasible in this codebase.
> - `uncertain`: cannot be decided from the repository alone
>
> Then list real issues `<other>` MISSED — defects AND bad design decisions — at most 5, only ones you can defend; ids `<critic>-missed-<n>`.
> Return ONLY JSON: `{"verdicts":[{"issueId","verdict","reasoning" (max 2 sentences, cite file:line)}],"missedIssues":[<findings>],"summary"}`

Codex down or `--no-codex` → spawn a *fresh* `general-purpose` agent as critic name `critic`, appending: "You are a fresh, independent stand-in for the unavailable second model. You share no context with the reviewer — critique with full hostility." Never skip this side: no finding may reach the judge uncontested.

**Disputed** = a finding whose latest verdict is `invalid` or `uncertain` and whose author has not conceded it. No disputes → go to Step 4.

**Rounds 2–3.** Each side gets one call and does two jobs: answer the attacks on its own findings, and re-verdict the defences it received last round.

> Round `<n>` of an adversarial review debate. You are "`<side>`".
> `<the context block>`
>
> [when the side has disputed findings: Your findings the other reviewer disputes, with its reasoning: `<JSON>`. For each: `concede` or `defend`.]
> [when the side disputed the other's findings: Findings of yours that the other reviewer defended last round, with its new evidence: `<JSON>`. For each, re-verdict `valid` / `invalid` / `uncertain`.]
>
> - Concede ONLY when the other side's evidence actually shows the finding is wrong, already handled, or pre-existing — name the file:line you checked. Deferring to the other reviewer, or conceding to end the argument, is not a resolution: if you still believe the finding, defend it and let the judge decide.
> - Defend ONLY with evidence you have not already given — a file you opened, a caller you traced, a case the other side's reasoning does not cover. Repeating your original claim louder is a deadlock, so say plainly that your position is unchanged instead.
> - Changing a verdict works the same way: new evidence, cited, or say your verdict stands.
> Return ONLY JSON: `{"positions":[{"issueId","stance":"concede|defend|valid|invalid|uncertain","reasoning" (max 2 sentences, cite file:line),"newEvidence": bool}],"summary"}`

After each round, settle what you can and stop when any of these holds:

- **No disputes left** — every finding is agreed valid, or its author conceded it.
- **Nothing moved** — a whole round in which no stance changed and no `newEvidence` was offered. That is deadlock; the judge arbitrates.
- **Round 3 reached.**

Then: conceded findings are dropped and never reach the judge. Surviving findings carry `settled` — `agreed` (the critic came to `valid`), `conceded-by-critic` (the critic withdrew an `invalid`), or `deadlocked` — plus the round number that settled them.

## Step 4 — Synthesis judge

Thread each surviving finding with its final verdict — `criticVerdict` (`valid`/`invalid`/`uncertain`, or `uncritiqued` when no one addressed it), `criticReasoning`, `settled`, and `rounds` — and pass the debate record for anything `deadlocked`. Spawn one `general-purpose` agent, model per the effort table:

> You are the synthesis judge of an adversarial review between "claude" and "codex". Each finding below carries its critic's verdict. Produce the final verdict.
> `<the context block>`
>
> Debate record: `{"claudeIssues":[...threaded],"codexIssues":[...threaded],"missedByClaude":[...],"missedByCodex":[...]}`
>
> Rules:
> - Same underlying issue found by both sides in round 1: confirm once, agreement `both`, merged under one id, merged ids named in the description. That is two reviewers landing on it independently — the strongest signal in the record.
> - Agreement reached *during* the debate is weaker than that, because a side that changed position may simply have yielded. Treat `settled: agreed` and `settled: conceded-by-critic` as one reviewer's finding that survived an argument, not as corroboration, and check the concession cites file evidence — where it does not, verify the finding yourself.
> - Tiered verification — spend file reads where the stakes are:
>   * every `high`, plus any `medium` that is `deadlocked`, `uncertain` or `uncritiqued`: VERIFY YOURSELF in the actual files before deciding. On a `high` no one independently corroborated, spend that read trying to REFUTE it — hunt evidence it is already handled or pre-existing rather than introduced — and reject it unless it survives.
>   * `medium` settled `valid`: confirm unless obviously wrong.
>   * `low`: decide on the debate record alone, no file reads — settled valid → confirm, anything else → reject as unvetted.
> - `deadlocked` findings are yours to arbitrate: both sides gave their best evidence and neither moved, so the record will not settle it — the files will.
> - `missedIssues` are candidates (agreement = the side that raised them), held to the same tiers.
> - Design issues: confirm only if the alternative is feasible in this codebase and materially better — then it deserves the same weight as a defect, do not drop it as taste.
> - Reject anything without a concrete failure scenario or concrete better alternative.
> - [effort low] STRICT: confirm ONLY findings a maintainer would block the merge over; reject the rest with reason "below strict bar".
> - Each confirmed issue gets a specific, actionable `fixRecommendation`.
> - Return ONLY JSON: `{"confirmed":[{<finding fields>,"agreement":"both|claude-only|codex-only","fixRecommendation"}],"rejected":[{"id","reason"}],"summary"}`

Nothing confirmed → `clean`. Report-only run with findings → `issues-found`, report and stop.

## Step 5 — Fix loop (`--fix` only)

Snapshot `git status --porcelain` — the mutation guard needs the before state, or a `working-tree` target's own dirt reads as the fixer's. Then spawn one `general-purpose` agent (model: inherit):

> Apply fixes for the confirmed findings of an adversarial review. Edit the files under review (source code or documents) in place.
> `<the context block>`
> Confirmed findings: `<JSON>`
>
> Rules:
> - Minimal, targeted fixes; follow each `fixRecommendation` unless the actual files contradict it — then fix the underlying issue properly and note the deviation.
> - Do not refactor beyond the fix. Do not fix anything not listed. Do not touch files no finding names unless a fix strictly requires it (then say so in notes).
> - Skip (with reason) anything that turns out wrong or needs a product decision.
> - Afterwards run `git status --porcelain` and report EVERY modified/created file in `changedFiles`, exactly as git prints the paths.
> - Return ONLY JSON: `{"fixed":["ids"],"skipped":[{"id","reason"}],"changedFiles":["paths"],"notes"}`

Three guards, then loop back to Step 2:

- **Mutation guard.** Take `changedFiles` minus the snapshot — what the fixer actually touched. Anything there outside the files the confirmed findings name → stop the run as `scope-violation` so the user can inspect the working tree, instead of letting the next iteration bless drift.
- **Anti-anchoring memory.** Accumulate `{file, title}` for every finding actually fixed and pass the list into the next iteration's review brief, so fresh passes hunt what was missed instead of re-debating what was fixed.
- **Stagnation breaker.** Fingerprint the confirmed set as sorted `file|title` pairs. An iteration confirming the same set as the previous one, or a fixer that fixed nothing → stop as `stagnant`.

Three iterations exhausted with findings still open → `max-iterations`.

## Report

Write the run record — `{status, target, iterations, rounds, effort, codexAvailable, confirmed, rejected, conceded, fixed, summary}` — to a temp file and give the path: a 30-minute run should leave a machine-readable artifact rather than only prose.

- Status — `clean` / `issues-found` / `stagnant` / `max-iterations` / `scope-violation` / `nothing-to-review` / `error` — and iterations run. If the Codex leg never ran, say the debate was single-model and why (`codex login` restores it). `scope-violation` = the fixer touched files no finding names; the run stopped.
- How the debate ended: rounds run, and whether it agreed, deadlocked, or hit the round cap. Name anything the judge had to arbitrate — that is where the two models could not be reconciled, and it is worth the user's attention.
- Each confirmed finding: kind (`defect`/`design`), severity, `file:line`, title, agreement (`both`/`claude-only`/`codex-only`), how it settled, fixRecommendation.
- Findings one side withdrew: id and title only, one line. They were real enough to raise and are worth a glance.
- Fix mode: fixed vs. still open.

Do NOT re-review or second-guess the findings. Do NOT apply fixes in report-only mode unless the user then asks.
