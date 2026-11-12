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

Use [review procedure](#review-procedure) only when fresh scrutiny is warranted. Research directly by default; batch independent tool calls. For bulky sources or separable questions, use the conditional dispatch in [research scouts](#research-scouts). Scouts gather evidence; the planner owns synthesis. Neither agents nor a particular model/provider are required.

- **`--review`:** judge a supplied plan against the user's requested outcome and scope; preserve it unless editing was requested. Reuse valid evidence rather than restarting discovery.
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

Establish the relevant current baseline, what can be reused and what changes. Explain how the chosen approach achieves the outcome. For system designs and implementation handoffs, decide the cooperating responsibilities, meaningful inputs and outputs, ownership, interactions and important lifecycle/failure behavior. Define the contracts and rules that make the design work; component names and desired properties alone do not explain a mechanism.

Use a compact example, state model or data shape when it expresses a consequential decision more clearly than prose. Use an editable Mermaid diagram when relationships benefit; distinguish current from proposed behavior, check prose agreement and render/check syntax when available, reporting if unrendered. Leave routine file layouts, helper signatures, code bodies and detailed test matrices to implementation unless they determine a consequential contract, requirement or feasibility. An example is illustrative unless its exact form is required.

Derive execution deliverables from the design and its dependencies. Each meaningful increment names its result, prerequisites and observable acceptance; combine setup steps with the outcome they serve. Prefer an early end-to-end slice where it resolves integration risk, while allowing necessary prerequisites and migration work. Keep the overall design distinct from the first implementation slice. Research plans need discriminating observations and decision rules; product plans need intended behavior, outcome hypotheses and guardrails. Visions need priorities and next validation, without invented delivery certainty.

## Check and resolve

Check requested-outcome coverage, necessary scope, unsupported additions, dependencies, existing contracts, acceptance and diagram/prose agreement. Use the bounded procedure in [review procedure](#review-procedure) if fresh scrutiny is warranted. Never role-play personas as independent reviewers; if unavailable, self-check and disclose the limitation.

For system designs and implementation handoffs, trace representative normal and material failure or ambiguity cases through the chosen mechanisms to their observable results. Check that execution would not require inventing central design decisions. Label reasoned walkthroughs separately from executed checks; keep smaller reviews proportionate.

Resolve findings against sources, preserving material uncertainty and dissent. Changed conclusions need evidence or an identified reasoning error; agreement is not proof. User-value tradeoffs belong in the decision list. Stop when disputes are settled, a round adds no evidence or correction, or the review cap is reached.

## Deliver the plan

Lead with the recommended direction, why it matters and what changes. For substantial work, a useful default structure is: intended result and scope, relevant baseline, proposed solution and decisions, delivery sequence, acceptance, and material uncertainty. Merge, reorder or omit parts to fit the subject; do not fill empty sections. For several initiatives, make priority and rationale clear.

- **Make each idea scannable.** For a plan with several substantive parts, use named sections or distinct items. State each idea's purpose, then its decisive details and conditions. Split separately assessable responsibilities, decisions or checks; avoid burying several topics in one paragraph. Use prose for connected reasoning, tables for comparisons and examples for abstract ideas. Establish main behavior before exceptions.
- **Select detail.** Give central ideas the depth needed to understand or decide; keep smaller changes brief. No word cap, fixed headings, equal-size sections or milestone quota. More scrutiny need not lengthen the plan.
- **Give each fact one home.** Keep the current plan coherent; link bulky research, verification receipts and superseded history. Keep binding decisions, rationale and consequential caveats beside the design they qualify; do not hide them in links or add a code appendix by default.

Resolve choices that would change the approach, feasibility, compatibility, acceptance or delivery sequence. For genuine blockers, give stable IDs (`D1`, `D2`), options, a recommendation if supportable, the bounded observation and decision criterion needed, and affected work. Naming a preferred option does not settle an unsupported essential capability. State readiness for the requested scope and any independently ready slice separately; routine implementation checks may remain pending. Preserve decisions, exclusions and corrections during synthesis. Before handoff, check that a reader can explain the proposed behavior, find the next useful delivery and judge completion without reconstructing the conversation. Scan for repetition and lost substance; verify moved detail exists at its destination. Leave already-clear content alone.

Save substantive work and reconcile meaningful Q&A using [records.md](records.md), keeping one canonical plan with outcomes initially pending. Report the session/plan link and ID, checks actually performed, limitations and stop reason. Report usage when available; otherwise count scout calls, review calls and checks separately. These are work proxies, not measured savings or enforced billing limits.

## Research scouts

Use scouts for bulky sources or separable questions; keep cheap lookups and tightly coupled reasoning in the planner. Direct research and parallel tool calls are the default. If delegation is unavailable, research directly and expose material coverage gaps.

### Dispatch

Default to **at most two scout calls total, including follow-ups**, unless the user sets another research budget. The cap spans research rounds and is separate from review; increased scrutiny does not reset it. No recursive delegation.

Give each scout:

- One decision-relevant question, necessary constraints, distinct source scope and stop condition. Avoid overlapping searches unless checking a disputed claim.
- Read-only source access and specified non-destructive checks; writes only to designated scratch evidence. No implementation, external mutations or further agents.
- A compact evidence packet, usually 300–500 words, linking larger material without omitting consequential caveats.

Inherit the available model. Use a cheaper model only when authorized and adequate; do not install a provider or require a weaker model. Continue independent work while scouts run.

### Return and reconcile

The packet contains findings with evidence status, source/version pointers, executed checks and limits, contrary evidence, remaining gaps and the cheapest useful next observation.

Open the underlying sources for decisive claims and resolve material contradictions. Verify consequential or suspicious results through the cheapest useful check; do not repeat the whole investigation. Attribute scout-run checks and label inaccessible support as a gap.

Two scouts repeating one origin do not corroborate it. A scout cannot be the fresh critic of its own work; follow [review procedure](#review-procedure) separately when needed.

Record scout calls, checked evidence, gaps and the stop reason. At the cap, deliver the supported conclusion with its limits; do not silently expand the budget or claim complete coverage.

## Review procedure

Use fresh contexts with the task, constraints, intended decision and evidence pointers. The parent owns the plan; reviewers return findings. Access is read-only except designated scratch output. A research scout cannot review its own work as a fresh critic.

### Fresh critic

Freeze the draft and dispatch one critic:

> Assess readiness for the user's requested outcome and scope, supplied alongside the draft; do not infer a narrower assignment from the draft. Open relevant sources. Check coverage, unnecessary scope, missed reuse, unsupported claims, dependencies, failure paths, existing contracts, acceptance and diagram/prose agreement. Suggest a smaller alternative only when it preserves the goal. Preserve explicit constraints and requested breadth; flag lost decisions or guesses presented as commitments. Distinguish observed behavior from proposals and future checks.
>
> For system designs and implementation handoffs, distinguish chosen mechanisms from desired properties, trace representative cases and flag central choices left to execution. Separate readiness of the whole requested design from an independently ready slice or feasibility investigation. Require code-level detail only when it determines a consequential contract, requirement or feasibility. An exploration needs priorities and next evidence; execution plans need dependency-ordered results and acceptance. Flag repetition or overloaded items that obscure the design, rationale or next step; preserve substance without enforcing headings or length.
>
> Return at most five material findings, each with an affected claim, source, consequence and resolving correction or observation. No finding is required. Label uncertainty and give a short verdict: ready, revise or unresolved. This is advice, not implementation authorization.

Verify findings against evidence and correct supported issues. Allow **one targeted follow-up** only if a consequential correction needs checking. Otherwise stop; do not add reviewers because none found a defect.

### Blind alternative and dispute

For costly reversal or consequential disputed assumptions, retain any existing critic and add an alternative author. Give it the same brief and source access, **without the draft, favored option or critic findings**:

> Independently recommend the smallest credible approach. Inspect sources; identify the strongest alternative, decisive tradeoff and observation that would change your choice. Surface at most five material assumptions or failure scenarios with evidence or an explicit unknown. Return a compact recommendation, not another full plan. Do not consult the other reviewer before returning it.

Freeze the parent's draft before either result arrives. Keep initial judgments separate, including when contexts run sequentially. Prefer an available different model family only when authorized; do not install providers or incur a new paid service for diversity. Reusing one reviewer for both roles is not independence.

Deduplicate findings and challenge only disagreements that could change the plan or leave acceptance unsupported. Send each reviewer the opposing evidence and request:

- **Accept/correct:** identify the error that changes the position.
- **Defend:** provide new evidence or corrected inference and its consequence.
- **Unresolved:** name the missing observation or user-value choice.

Allow **at most two dispute rounds within six total review calls**, including initial calls and earlier critic follow-ups. Escalation never resets the count. Stop sooner when settled or a full round adds no evidence or correction. The parent adjudicates from sources; preferences can resolve value choices, not empirical uncertainty. Preserve unresolved dissent and the cheapest next check.

### Receipt

Record why review was useful, actual contexts/calls, known model diversity, changes caused by review, unresolved findings and stop reason: `settled`, `no-new-evidence`, `cap` or `review-unavailable`. If unavailable or prohibited, self-check and state the reason. Keep evidence pointers, not private reasoning transcripts. Review agreement does not establish implementation correctness or planning benefit.
