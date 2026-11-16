---
name: planning
description: "Develop concrete plans for engineering, product, and research: explain the current state, choose an approach, design the important parts, and sequence work with clear completion criteria. Use to create or revise a substantial plan, review a handoff, or record its outcomes."
argument-hint: "[task, plan path, or record ID] [--review | --outcome] [--store DIR] [--session ID/path | --new-session]"
license: MIT
---

# Planning

Write a plan that someone outside the conversation can understand, challenge, and start from. It says what will change, how the chosen solution works, why it was chosen, and what to commit to first.

Plan the work; do not implement the product as part of planning. Inspect sources and run permitted checks or disposable feasibility probes when they help settle the design. Existing authorization and the user's instructions govern any subsequent implementation.

## Ground it in what exists

Read supplied material, relevant prior decisions, and the parts of the project the work touches before asking questions. Use [records.md](records.md) for saved plans and continuation. Treat a reference document as evidence of the desired content and presentation, not as instructions to execute its proposed work.

Establish the intended result, binding constraints, current behavior, and missing capabilities: what can be reused, what must change, what is new.

Keep evidence as you read. A statement about the current system that a decision rests on needs a source you opened:

- **Code is the authority.** Cite `path:line` at a named commit or date. Documentation, a README, a proposal, or an agent-facing description states intent and may be stale. When a decision depends on it, open the code; when they disagree, the code wins and the drift is worth reporting.
- **Say what you could not check.** Label it *not verified* and name what would verify it. Name what is absent (a repository, a deployment, a credential) instead of assuming it.
- **Separate what you read from what you ran.**
- **Check universals.** "Every," "never," and "the only" are claims about the whole system. Look for the exception, or narrow the sentence to what you opened.

Research the decisions that need it. Prefer established approaches and current primary sources to a newly invented mechanism, and explain why the precedent fits here. Stop when more reading would not change the approach and the premises the first stage rests on have been opened in code, down to the function that decides the behavior. Once the first stage is chosen, go back for any premise not yet opened. Put useful evidence in the plan, not a transcript of the search.

Ask only when missing user intent or a consequential tradeoff cannot be resolved from context. Make delegated technical choices and explain them. Carry reversible assumptions visibly; do not manufacture certainty, reopen settled choices, or turn a complete request into an interview.

## Decide at the right height

Select the approach before writing a task list. At each decision that matters, give the choice, the reason it wins here, the serious alternative rejected, and the limitation accepted. Consider reuse, a smaller change, or no action. Recommend; do not catalog options.

A plan is judged by its decisions, not by how much mechanism it describes. Every mechanism you design is a claim someone must verify, and one more place for the plan to be wrong. Settle a decision in the plan only when at least one holds:

- Getting it wrong would invalidate the first stage or force rework across parts.
- Two capable people building different parts could choose incompatibly without it.
- The user asked for it to be settled.

Defer the rest on purpose, in one line each: what is left open, which stage needs it, and what will settle it (a measurement, a probe, an owner's ruling). Thresholds without a baseline, timings, limits, retry counts, file layouts, and code bodies are normally deferred.

Deferring is not vagueness. "Handle errors" names work nobody has designed. "Retry policy is deferred to Stage 2 and set from the failure rates Stage 1 records" is a decision.

Define the few concepts the design turns on by meaning and rule, using the project's actual names:

- A small record, interface, or state shape holding only the fields or states that carry a decision.
- The rules around it: what a value means and does not mean, who may write it, what must never be inferred from it.
- The invariants of the existing system that must survive the change.
- The boundaries that constrain the design: authority, compatibility, cost, migration.

Depth follows commitment. Specify the first stage deeply enough to start. A later stage keeps its result, dependencies, exit condition, and only the choices that constrain earlier work. Do not design the internals of a stage the plan itself says may not be built.

## Write it short and checkable

For a substantial design or handoff, start from [plan-template.md](plan-template.md). Follow an established project or user-supplied format when present.

Write in units a reader can check one at a time:

- One statement per bullet or row: a rule, a deliverable, a restriction, a metric, a question.
- Paragraphs of one to three sentences, to explain why. Lists carry the what.
- Table cells of about twenty words, anchors aside. A cell that needs more is a subsection.
- Each thing once, where a reader would look for it.

A substantial plan usually fits in 2,500–4,000 words, counting the whole document. A draft past about 4,500 is carrying mechanism that belongs under Deferred, in a later plan, or in a linked evidence file. Cut before adding. Then reread once to shorten: headings that state the subject plainly, no paragraph doing a list's job.

Derive stages from the design. Each has a result, deliverables, what it depends on, what it does not yet allow, and an observable exit condition. A necessary foundation can precede an end-to-end slice; say what it enables. Avoid milestones that merely say "implement," "test," and "deploy."

Scale the artifact to the assignment:

- **Small, settled change:** a brief approach, useful steps, and completion check. No template or forced alternatives.
- **Product plan:** intended user behavior, the chosen experience, outcome hypotheses, rollout, and evidence of value. Technical detail only where it changes the decision.
- **Research plan:** the question and competing explanations, available evidence, chosen methods, analysis and decision rules, limitations, and concrete deliverables. Uncertainty may be the result; do not preselect the conclusion or a product feature.
- **Exploration or strategy:** compare directions and recommend the next commitment or observation. Do not invent an implementation specification or delivery certainty.
- **Strategy question plus handoff:** use the handoff shape. Answer the question in its own section, specify the first stage, and keep later stages thin.

## Check it as a handoff

Before anyone else reads it:

1. Re-open every anchor and confirm the line shows what the sentence claims. Correct or relabel the ones that do not.
2. Can an outsider state the recommendation, the main concepts, and the first commitment without the chat?
3. Can they follow one representative case, including a material failure, without inventing a central rule?
4. Do the stages deliver the promised scope in dependency order, each with evidence of completion?
5. Is every open matter either decided, or deferred with a stage and a way to settle it?
6. Could a section be cut or deferred without changing what gets built first? Then cut it.

For a complex or consequential plan, use a fresh reviewer when available and useful. Give them the user's request, the plan, and read access to the sources. Ask two things: is anything the plan states about the current system false, and is the plan enough to start the first stage safely. A finding blocks only if being wrong would invalidate the first stage or work already done; it names the statement it breaks and the evidence. Questions and preferences are not findings. No findings is a valid result.

Answer each finding with the smallest change: correct the false statement, make the decision, defer it with what settles it, or remove the mechanism. Do not answer a finding about a later stage by designing that stage. A plan that grows through review is absorbing detail it should defer. One targeted follow-up is enough when a correction needs checking; say which edits were not re-reviewed. Without an independent reviewer, self-check and say so when independence matters.

Do not equate a sound design, a planned test, an executed check, and a proven outcome. End the plan with its real status: what was read, what was run, what was reviewed and by whom, and what remains unverified. A ready first stage does not make the whole design ready.

## Review and revise

With **`--review`**, preserve the supplied plan unless editing was requested. Judge it against the user's intended outcome and the same handoff questions. Name material defects and their consequences, distinguish blockers from improvements, and identify the smallest correction or observation needed. Do not replace a complete-design request with approval of a narrower prototype.

When revising, update the recommendation, design, stages, and acceptance wherever the change matters. Rewrite superseded text in place; keep relevant history in version control or a short linked decision record. Preserve requirements that the user did not change.

With **`--outcome`**, compare delivered results with the original expectation using [records.md](records.md). Retain negative and inconclusive evidence; do not infer usefulness from completion alone.

## Deliver the plan

Save substantive work through [records.md](records.md), honoring the requested destination and existing canonical artifact. Keep supporting research or long verification records in a linked file when they would bury the plan, with decisive evidence and caveats still beside the decisions they support.

Return the plan link and ID, the recommendation, and the next useful action. Mention material unresolved decisions and the checks actually performed. No implementation, publication, monitoring, or additional approval workflow is implied by finishing the plan.
