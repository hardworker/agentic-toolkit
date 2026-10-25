---
name: planning
description: Create or review concise, evidence-backed plans for engineering, product, and research, with useful diagrams, serious alternatives, and scrutiny matched to the stakes. Use for nontrivial planning, comparing approaches, checking a plan, or recording its decisions, outcomes, and lessons in a user-wide library.
argument-hint: "[task, plan path, or record ID] [--review | --outcome] [--store DIR] [--session ID/path | --new-session]"
license: MIT
---

# Planning

Deliver a plan the user can understand, challenge, and use for the decision at hand: a recommendation, its evidence and alternatives, the shape of the work, and checks that could expose a mistake. Preserve decisions and observed outcomes for later planning.

While planning, inspect code and run permitted non-destructive checks, but write only planning artifacts and disposable probes; do not edit product code, tests, or configuration. Implementation belongs to a separate, user-authorized phase or handoff, even when the same agent performs it. These are role instructions, not a filesystem sandbox.

## Match scrutiny to the task

Read the relevant existing work, then infer the useful checks from uncertainty, consequences, reversibility, and dependencies. Choose the scrutiny directly; do not ask the user to select a level. Honor stated time, cost, scope, and delegation limits, and disclose any consequential verification gap they leave.

| Task context | Useful scrutiny | Review budget |
|---|---|---|
| Clear, bounded, reversible work | Source checks and self-check | No review agents |
| Meaningful alternatives or dependencies that a fresh check could challenge | Add one fresh critic | At most one targeted follow-up |
| Costly reversal or consequential disputed assumptions that could change the approach | Add a blind alternative alongside the critic | At most two dispute rounds; six review calls total |

For a straightforward action with no meaningful planning decision, give the few steps it needs. Reassess as evidence arrives: add scrutiny only when it could change the plan or resolve a consequential gap, and explain the specific risk it addresses. A targeted source check may settle a question without another reviewer. Existing calls count toward the caps when scrutiny increases. These budgets are a starting policy, not a measured optimum.

`--review` checks a supplied plan against its goal and evidence. Preserve the original unless editing was requested; return material findings and proposed corrections. Reuse valid prior evidence and decisions instead of restarting discovery.

`--outcome` (or a request to record results or lessons) updates an existing record using [records.md](records.md). Match the record before writing; record known results and gaps without restarting planning or launching a review council. Review a disputed claim only when it could change the recorded conclusion. If review and outcome capture are both requested, preserve the supplied plan and distinguish proposed corrections from observed results.

## Ground the decision

1. State the desired outcome, constraints, non-goals, and observable success. Distinguish the user's decisions from your assumptions. For substantive planning, read [records.md](records.md) and look up relevant prior decisions and outcomes; recheck their applicability and evidence. Inspect discoverable facts yourself. Ask only for missing decisions that could change scope, approach, acceptance, or a costly commitment; batch independent questions and recommend answers. Carry minor reversible choices as explicit assumptions.
2. Inspect the sources that bear on those decisions: code and tests for existing behavior, the actual document/data for a named artifact, and current primary sources for external facts that may have changed. Follow the user's research scope. An explicit broad comparison warrants a broad scan followed by deeper checks of the shortlist.
3. Record material claims with an evidence pointer and status. Use **observed**, **tested**, **inferred**, **assumed**, or **unknown**; add **corroborated** only when evidence has independently originating support. These are provenance labels, not a confidence scale. A test establishes only the behavior it exercises; two pages repeating one source count as one origin.
4. For claims that determine the recommendation, look for disconfirming evidence or another evidence channel. Resolve a disputed fact with the cheapest useful observation. Existing non-destructive checks and disposable probes may help when within the task's permissions; don't change the product to make a plan look verified. Record the command, result, scope, and version/commit where relevant. A proposed future check is never an executed result.

Bound research by decisions: expand only when a missing fact could change an option, leave a consequential criterion unsupported, or satisfy the user's requested breadth. Separate unknown facts from user preferences. If a blocker affects only part of the plan, finish the independent parts and make the dependency explicit.

Research directly by default; batch independent tool calls before adding agents. Use research scouts when bulky sources would crowd out decision-making or questions can be investigated independently. If that would help and delegation is permitted, read [scouts.md](scouts.md) for the bounded dispatch and evidence contract. Scouts gather evidence; the planner still owns synthesis and checks the sources that determine the recommendation. Research breadth and review depth are separate choices.

## Compare, sketch, and sequence

Compare the smallest viable approach, including reuse or doing nothing where credible, with a serious alternative. Explain the deciding tradeoff and what would reverse your recommendation. Do not invent a second option when constraints leave only one viable path; say why the alternatives fail.

Keep the architectural view: major components or stages, responsibilities, interactions, and consequential data, trust, or operational boundaries. Use a small editable Mermaid diagram when it makes those relationships clearer; show the main flow rather than every branch. Mark current versus proposed behavior. Check important edges/states against the prose and evidence; render/check syntax when a renderer is available, and don't claim rendering when it wasn't checked.

Match commitments to the plan's purpose and maturity. A vision or early exploration needs priorities, consequential dependencies, and the next decision or validation; do not invent delivery certainty. For execution-ready work, define deliverables in dependency order, each with its prerequisite and observable acceptance condition.

Specify architectural decisions and constraints that affect feasibility, scope, or acceptance. Leave file layouts, function signatures, field schemas, code snippets, and detailed test matrices to the implementer. Existing code paths may be cited as evidence; they are not a file-by-file work plan. If implementation reveals a conflict with the agreed architecture or acceptance conditions, return that decision for resolution.

Adapt to the domain:

| Engineering | Product | Research |
|---|---|---|
| Components, responsibilities, system boundaries | Audience, outcome hypothesis, rollout | Question, source criteria, competing explanations |
| Acceptance conditions, operational limits, rollback | Observable outcome and guardrail metrics | Discriminating observations and falsification |
| Technical dependencies | Learning and adoption dependencies | Evidence and experiment dependencies |

## Challenge and resolve

First check coverage of the requested outcome, dependencies, existing contracts, source support, and diagram/prose agreement yourself; check deliverables and acceptance when execution is being planned. Self-checking remains useful even when independent review follows.

When fresh scrutiny is warranted, read [review.md](review.md) and request the bounded review it defines when the host permits delegation. Give reviewers a compact brief and evidence pointers, not the full conversation. Keep initial judgments separate. For a blind alternative, prefer an already available different model family when authorized; do not install a provider or incur a new paid service merely to fill a role.

If fresh reviewers are unavailable or prohibited, perform the strongest permitted check and report **self-checked; independent review unavailable** with the reason. Never role-play multiple personas and call them independent. State whether actual reviewers used the same model, different models, or unverified model identities.

Resolve material findings against sources. A changed stance needs new evidence or an identified reasoning error. Stop debate when no material dispute remains, a round brings no new evidence or corrected inference, or the review cap is reached. Preserve unresolved dissent with its consequence and cheapest next check; votes and agreement are not proof. User-value tradeoffs belong in the decision list, not the defect list.

## Deliver a readable, inspectable artifact

Orient the reader to the proposed direction, why it matters, and what changes from the current situation. For multiple initiatives, make relative priority and its rationale clear. Keep scope, serious alternatives, architectural boundaries, acceptance conditions, and material uncertainties visible where relevant.

- **Selective depth:** spend space where it helps understanding or changes a decision. A central concept may need explanation, examples, and architectural detail while a smaller proposal needs only a few lines. No word target, equal-size sections, or milestone quota; more scrutiny need not lengthen the brief.
- **Useful grouping:** organize around the reader's decisions and the subject: initiatives, capabilities, options, questions, or delivery stages as appropriate. Familiar labels can help navigation, but neither a supplied example nor the planning workflow dictates the headings. Make the next action easy to find.
- **Explain the proposal:** make clear what it means, why it helps, and how it fits existing work. Establish the main behavior before its exceptions. Use a concrete example or short scenario when it makes an abstract idea understandable. These are useful questions, not mandatory subsections for every item.
- **Meaningful items, direct wording:** use plain language and compact lists for points the reader can assess or act on separately, such as decisions, changes, responsibilities, or checks. Keep relevant rationale and essential conditions with their point; separate unrelated points. Use focused prose for connected explanation, tables for comparisons, and diagrams for relationships. Rewrite tangled sentences; adding bullets or bold labels alone does not make a block readable. Avoid reducing explanations to fragments.
- **One home for each fact:** reference decisions and constraints instead of repeating them across sections. Use clearly named supporting sections or links for detailed cases, verification, evidence, and review receipts when they interrupt the main explanation. Keep constraints and caveats that change the decision beside the claims they qualify; a link must not hide them. Do not add a code-level implementation appendix by default.

Give unresolved choices stable IDs (`D1`, `D2`), options, a recommendation, and what they block; settled choices become constraints. Include checks and review actually performed, important limits, and the stop reason.

Before handoff, read the headings and opening lines, then scan each block: can the reader find what is proposed, why, how it fits together, what happens next, and what remains unresolved? Check that shortening or moving detail preserves decisions, rationale, scope, dependencies, acceptance, uncertainty, and authority boundaries. Verify moved content exists at the linked destination. For readability edits, leave already-clear content alone; do not enforce paragraph lengths or a fixed heading scheme.

Save substantive plans and their decisions in the user-wide library using [records.md](records.md), with an outcome initially marked pending. Default to `~/.local/share/grounded-plan/`; an explicit `--store DIR` or `GROUNDED_PLAN_HOME` can override it. Honor an explicit artifact destination or request not to save. Existing plans remain at their original paths and can be referenced by a library record; do not migrate or duplicate them automatically. Maintain one canonical plan, preserve original expectations and dated decisions, and reread the record after context loss. Use the named-session registration/continuation contract in `records.md`; honor `--session ID/path` and start separate work with `--new-session`. Refresh the compact entry after substantive continuation/delivery, including optional read-only learning discovery when available. Return the session entry, relevant plan link, and record ID. If access is unavailable, report the unsaved record rather than silently storing it in the repository.

Report actual token/tool usage when available. Otherwise give work proxies, counting scout calls, review calls, and checks separately. Do not invent prices or cost savings. Agent limits are instruction-level budgets, not host-enforced billing limits. Recheck changed decisions and affected evidence; don't replay the whole process for cosmetic revisions.
