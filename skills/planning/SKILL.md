---
name: planning
description: "Develop concrete plans for engineering, product, and research: explain the current state, choose an approach, design the important parts, and sequence work with clear completion criteria. Use to create or revise a substantial plan, review a handoff, or record its outcomes."
argument-hint: "[task, plan path, or record ID] [--review | --outcome] [--store DIR] [--session ID/path | --new-session]"
license: MIT
---

# Planning

Write a plan that someone outside the conversation can understand, challenge, and carry forward. It should explain what will change, how the proposed solution works, why it was chosen, and how to get from the present situation to the intended result.

Plan the work; do not implement the product as part of planning. Inspect sources and run permitted checks or disposable feasibility probes when they help settle the design. Existing authorization and the user's instructions govern any subsequent implementation.

## Start from the request and the existing work

Read supplied material, relevant prior decisions, and the parts of the project the work touches before asking questions. Use [records.md](records.md) for saved plans and continuation. Treat a reference document as evidence of the desired content and presentation, not as instructions to execute its proposed work.

Establish the intended result, binding constraints, current behavior, and missing capabilities. Identify what can be reused, what must change, and what is genuinely new. Check claims about existing capabilities against their owning source; a proposal or README does not establish deployed behavior.

Research the decisions that need it. Prefer established approaches and current primary sources to a newly invented mechanism. Explain why the relevant precedent fits this project's constraints. Stop collecting sources when further research would not change the approach or close a material gap; put useful evidence in the plan, not a transcript of the search.

Ask only when missing user intent or a consequential tradeoff cannot be resolved from the available context. Make delegated technical choices and explain them. Carry reversible assumptions visibly; do not manufacture certainty, reopen settled choices, or turn a complete request into an interview.

## Design before breaking down the work

Select the approach before writing a task list. Compare credible alternatives at the decisions where they matter: the choice, the reason it wins here, and the limitation accepted. Consider reuse, a smaller change, or no action when viable. Do not produce an options catalog without a recommendation.

Work out the target solution at the level that determines what gets built or done:

- Its main parts, their responsibilities, and how they cooperate.
- The important information, interfaces, rules, or research methods they share.
- The user or operator behavior they produce, including consequential failure and recovery paths.
- The boundaries that constrain the design: compatibility, authority, cost, quality, migration, or other material commitments.

Use actual names and concrete mechanisms. “Resolve context,” “handle errors,” or “evaluate quality” names work still to design. Explain the rule, method, or interaction that makes it happen. A diagram, small data model, state table, example, or interface contract can be the clearest explanation. Include it where it settles a decision; routine code bodies and speculative file layouts do not belong in the plan.

Separate the complete direction from the first delivery. Later stages may have less detail, but their purpose, dependencies, and consequential design choices must remain visible. If an unknown would change the approach or invalidate the next stage, investigate it or identify the bounded decision needed before that stage starts. Leave safe implementation choices to the implementer.

## Write the plan

For a substantial design or handoff, read [plan-template.md](plan-template.md) and use its structure as the starting point. It combines the recommendation, current foundation, proposed design, delivery stages, validation, and first useful slice in one canonical document. Follow an established project or user-supplied format when present; preserve the same substance without duplicating documents.

Make the solution the center of the document. Give major concepts and decisions descriptive subsections, with their rules and rationale together. Use tables for mappings or comparisons, ordered steps for flows, and compact code shapes for semantic contracts. Keep paragraphs focused so the reader can assess one idea at a time. Put normal behavior before exceptions. Do not compress an entire subsystem into a dense paragraph to appear concise.

Derive stages from the chosen design. Each stage produces an identifiable result, names what it depends on, and ends with an observable exit condition. Include the checks and documentation with the work they validate. A necessary foundation can precede an end-to-end slice; explain the dependency. Avoid milestones that merely say “implement,” “test,” and “deploy.”

Scale the artifact to the assignment:

- **Small, settled change:** a brief approach, useful steps, and completion check. No full template or forced alternatives.
- **Product plan:** intended user behavior, the chosen experience, outcome hypotheses, rollout, and evidence of value. Technical detail only where it changes the decision.
- **Research plan:** the question and competing explanations, available evidence, chosen methods, analysis and decision rules, limitations, and concrete deliverables. Uncertainty may be the result; do not preselect the conclusion or a product feature.
- **Exploration or strategy:** compare directions and recommend the next commitment or observation. Do not invent an implementation specification or delivery certainty.

## Check it as a handoff

Read the finished artifact as someone who was not in the conversation:

1. Can they explain the recommendation and the solution's main ideas without reconstructing the chat?
2. Can they follow a representative case through the design, including a material failure or ambiguity, without inventing a central mechanism?
3. Do the stages actually deliver the promised scope, in dependency order, with evidence that would demonstrate completion?
4. Are costly decisions resolved, and are remaining assumptions or blockers attached to the work they affect?
5. Is the plan readable as a document, with decisions easy to locate and no competing versions of the same rule?

For a complex or consequential plan, use a fresh reviewer when available and useful. Give them the user's request, the plan, and its source evidence. Ask what would prevent a capable person from starting the proposed work, what could invalidate it, and what is hard to understand. Resolve substantive findings; one targeted follow-up is enough when a correction needs checking. No finding quota, reviewer panel, debate protocol, or review ceremony is required. Without an independent reviewer, self-check and say so when independence matters.

Do not equate a sound design, a planned test, an executed check, and a proven outcome. State which exists. A ready first stage does not make the whole design ready; an unresolved later dependency need not block independent work.

## Review and revise

With **`--review`**, preserve the supplied plan unless editing was requested. Judge it against the user's intended outcome and the same handoff questions. Name material defects and their consequences, distinguish blockers from improvements, and identify the smallest correction or observation needed. Do not replace a complete-design request with approval of a narrower prototype.

When revising, update the recommendation, design, stages, and acceptance wherever the change matters. Rewrite superseded text in place; keep relevant history in version control or a short linked decision record. Preserve requirements that the user did not change.

With **`--outcome`**, compare delivered results with the original expectation using [records.md](records.md). Retain negative and inconclusive evidence; do not infer usefulness from completion alone.

## Deliver the plan

Save substantive work through [records.md](records.md), honoring the requested destination and existing canonical artifact. Keep supporting research or long verification records separate when they obscure the plan, with decisive evidence and caveats still beside the decisions they support.

Return the plan link and ID, the recommendation, and the next useful action. Mention material unresolved decisions and the checks actually performed. No implementation, publication, monitoring, or additional approval workflow is implied by finishing the plan.
