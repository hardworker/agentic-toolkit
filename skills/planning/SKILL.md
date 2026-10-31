---
name: planning
description: Create or review concise, evidence-backed plans for engineering, product, and research, with useful diagrams, serious alternatives, and scrutiny matched to the stakes. Use for nontrivial planning, comparing approaches, checking a plan, or recording its decisions, outcomes, and lessons in a user-wide library.
argument-hint: "[task, plan path, or record ID] [--review | --outcome] [--store DIR] [--session ID/path | --new-session]"
license: MIT
---

# Planning

Produce a plan the user can understand, challenge and use: a recommendation, essential design, evidence, tradeoffs and next useful action.

Inspect code and run permitted non-destructive checks; write only planning artifacts and disposable probes. Product implementation belongs to a separate authorized phase or handoff, even with the same agent. This is a role boundary, not filesystem enforcement.

## Match scrutiny to the decision

Infer scrutiny from uncertainty, consequences, reversibility and dependencies. Honor the user's scope, time, cost and delegation limits; do not ask them to choose an effort level.

| Situation | Useful scrutiny |
|---|---|
| Clear, bounded, reversible work | Source checks and self-check |
| Material alternatives or dependencies | One fresh critic when it could change the plan |
| Costly reversal or consequential disputed assumptions | Add a blind alternative and bounded debate |

Use [review.md](review.md) only when fresh scrutiny is warranted. Research directly by default; batch independent tool calls. For bulky sources or separable questions, use the conditional dispatch in [scouts.md](scouts.md). Scouts gather evidence; the planner owns synthesis. Neither agents nor a particular model/provider are required.

- **`--review`:** judge a supplied plan for its intended decision; preserve it unless editing was requested. Reuse valid evidence rather than restarting discovery.
- **`--outcome`:** match the existing record and follow [records.md](records.md). Capture known results and gaps; investigate only disputes that could change the conclusion.
- **Simple requests:** give the few useful steps; no forced interview, objection or full planning process.

## Ground and shape the decision

1. **Separate outcome from mechanism.** Identify the problem, desired result, constraints and requested outputs. Distinguish accepted decisions from proposals, assumptions and observed facts. Challenge consequential unsupported premises before elaborating a solution; settled requirements remain constraints unless the user changes them.
2. **Resolve material uncertainty.** Read relevant prior work through [records.md](records.md). Inspect discoverable facts yourself; use current primary sources for external claims. Ask only for missing decisions that could change scope, approach, acceptance or a costly commitment. Batch independent questions, recommend answers and carry minor reversible choices as explicit assumptions.
3. **Check decisive claims.** Record source/version and status: **observed**, **tested**, **inferred**, **assumed** or **unknown**. Use **corroborated** only for independently originating support. Seek disconfirming evidence for claims that determine the recommendation; two retellings of one source are not corroboration. Record actual check results and limits; a proposed check is not an executed result.

Continue research or questions when they could change the decision, close a consequential evidence gap or fulfill requested breadth. Otherwise synthesize; wording polish need not reopen intake. Finish independent parts when a blocker affects only some work. Adapt depth to the plan's maturity: an exploration can end with the next observation or a reason to stop.

## Select scope and design

Compare the smallest viable approach, including reuse or no action where credible, with a serious alternative. Explain the deciding tradeoff and what would reverse the choice; do not invent an alternative when constraints leave only one viable path.

Ask what breaks if proposed work is removed. Include it for an outcome, prerequisite or consequential constraint. Explain material exclusions and when to revisit deferred work. Recommend changes to explicit requirements openly; narrowing one thread must not erase another requested output, a broad survey or a requested roadmap.

Keep the architectural view: components or stages, responsibilities, interactions, ownership, lifecycle and consequential boundaries. Use an editable Mermaid diagram when relationships are clearer visually; distinguish current from proposed behavior. Check it against the prose and evidence, and render/check syntax when a renderer is available; report if unrendered. Leave code layouts, signatures, field schemas and detailed test matrices to the implementer. Return conflicts affecting agreed architecture or acceptance for resolution.

For execution plans, sequence deliverables by dependency and define observable acceptance. An acceptance condition describes a finished result; merge steps that merely serve another outcome into it. Retain required methods as constraints and necessary design choices in the architecture. An example is illustrative unless its exact form is required. Research plans need discriminating observations; product plans need outcome hypotheses and guardrails. Visions need priorities and next validation, without invented delivery certainty.

## Check and resolve

Check requested-outcome coverage, necessary scope, unsupported additions, dependencies, existing contracts, acceptance and diagram/prose agreement. Use the bounded procedure in [review.md](review.md) if fresh scrutiny is warranted. Never role-play personas as independent reviewers; if unavailable, self-check and disclose the limitation.

Resolve findings against sources, preserving material uncertainty and dissent. Changed conclusions need evidence or an identified reasoning error; agreement is not proof. User-value tradeoffs belong in the decision list. Stop when disputes are settled, a round adds no evidence or correction, or the review cap is reached.

## Deliver the plan

Lead with the recommended direction, why it matters and what changes. For several initiatives, make priority and rationale clear. Keep essential design, serious alternatives, next action and unresolved choices easy to find.

- **Make each idea scannable.** For a plan with several substantive parts, use named sections or distinct items. State each idea's purpose, then its decisive details and conditions. Split separately assessable responsibilities, decisions or checks; avoid burying several topics in one paragraph. Use prose for connected reasoning, tables for comparisons and examples for abstract ideas. Establish main behavior before exceptions.
- **Select detail.** Give central ideas the depth needed to understand or decide; keep smaller changes brief. No word cap, fixed headings, equal-size sections or milestone quota. More scrutiny need not lengthen the plan.
- **Give each fact one home.** Link interrupting research, detailed cases and verification receipts. Keep consequential caveats beside their claims; do not hide them in links or add a code appendix by default.

Give unresolved choices stable IDs (`D1`, `D2`), options, a recommendation and what they block. Preserve decisions, rationale, exclusions and corrections during synthesis. Before handoff, scan headings and blocks for findability, repetition and lost substance; verify moved detail exists at its destination. Leave already-clear content alone.

Save substantive work and reconcile meaningful Q&A using [records.md](records.md), keeping one canonical plan with outcomes initially pending. Report the session/plan link and ID, checks actually performed, limitations and stop reason. Report usage when available; otherwise count scout calls, review calls and checks separately. These are work proxies, not measured savings or enforced billing limits.
