---
name: grounded-plan
description: Create or review concise, evidence-backed plans for engineering, product, and research, with useful diagrams, serious alternatives, and scrutiny matched to the stakes. Use for nontrivial planning, comparing approaches, checking a plan, or recording its decisions, outcomes, and lessons in a user-wide library.
argument-hint: "[task, plan path, or record ID] [--review | --outcome] [--effort lean|standard|deep] [--store DIR]"
license: MIT
---

# Grounded Plan

Deliver a plan the user can understand, challenge, and hand off: a recommendation, its evidence and alternatives, the shape of the work, and checks that could expose a mistake. Preserve decisions and observed outcomes for later planning. End with the requested artifact; continue into implementation only when the user has authorized that next action.

## Scope and effort

Read the relevant existing work before choosing depth. Say which mode you chose and why in one sentence. Honor an explicit budget or effort setting; the following adaptive default is a starting policy, not a measured optimum.

| Mode | Use | Review budget |
|---|---|---|
| `lean` | Clear, bounded, reversible work | Source checks and self-check; no review agents |
| `standard` | A substantive choice with meaningful alternatives or dependencies | One fresh critic; at most one targeted follow-up |
| `deep` | Requested thorough debate, costly reversal, or consequential disputed assumptions | Two fresh review contexts; at most two dispute rounds |

For a straightforward action with no meaningful planning decision, give the few steps it needs; do not expand it into this entire workflow. Default to standard for nontrivial planning. Use deep only when the added scrutiny can change the decision; explicit lean remains lean, with any consequential verification gap reported.

`--review` checks a supplied plan against its goal and evidence. Preserve the original unless editing was requested; return material findings and proposed corrections. Reuse valid prior evidence and decisions instead of restarting discovery.

`--outcome` (or a request to record results or lessons) updates an existing record using [records.md](records.md). Match the record before writing; record known results and gaps without restarting planning or launching a review council. Review a disputed claim only when it could change the recorded conclusion. If review and outcome capture are both requested, preserve the supplied plan and distinguish proposed corrections from observed results.

## Ground the decision

1. State the desired outcome, constraints, non-goals, and observable success. Distinguish the user's decisions from your assumptions. For substantive planning, read [records.md](records.md) and look up relevant prior decisions and outcomes; recheck their applicability and evidence. Inspect discoverable facts yourself. Ask only for missing decisions that could change scope, approach, acceptance, or a costly commitment; batch independent questions and recommend answers. Carry minor reversible choices as explicit assumptions.
2. Inspect the sources that bear on those decisions: code and tests for existing behavior, the actual document/data for a named artifact, and current primary sources for external facts that may have changed. Follow the user's research scope. An explicit broad comparison warrants a broad scan followed by deeper checks of the shortlist.
3. Record material claims with an evidence pointer and status. Use **observed**, **tested**, **inferred**, **assumed**, or **unknown**; add **corroborated** only when evidence has independently originating support. These are provenance labels, not a confidence scale. A test establishes only the behavior it exercises; two pages repeating one source count as one origin.
4. For claims that determine the recommendation, look for disconfirming evidence or another evidence channel. Resolve a disputed fact with the cheapest useful observation. Existing non-destructive checks and disposable probes may help when within the task's permissions; don't change the product to make a plan look verified. Record the command, result, scope, and version/commit where relevant. A proposed future check is never an executed result.

Bound research by decisions: expand only when a missing fact could change an option, leave a consequential criterion unsupported, or satisfy the user's requested breadth. Separate unknown facts from user preferences. If a blocker affects only part of the plan, finish the independent parts and make the dependency explicit.

## Compare, sketch, and sequence

Compare the smallest viable approach, including reuse or doing nothing where credible, with a serious alternative. Explain the deciding tradeoff and what would reverse your recommendation. Do not invent a second option when constraints leave only one viable path; say why the alternatives fail.

Use a diagram when relationships, order, state, or boundaries matter. Prefer a small editable Mermaid diagram: component/context for boundaries, sequence for interactions, state for lifecycle, dependency graph for order, decision tree for dependent choices. A table can be clearer for a simple comparison. Mark current versus proposed behavior. Check that every important edge/state agrees with the prose and evidence; render/check syntax when a renderer is available, and don't claim rendering when it wasn't checked.

Define independently checkable deliverables in dependency order. Usually a handful is enough; split further only when execution or review needs the boundary. Each identifies the affected area, its prerequisites, and an observable acceptance check. Read existing paths/interfaces before naming them; label new ones as proposed. Specify decisions an implementer cannot safely invent, not bodies of code that the interfaces and tests already determine.

Adapt to the domain:

| Engineering | Product | Research |
|---|---|---|
| Existing interfaces, files, migrations | Audience, outcome hypothesis, rollout | Question, source criteria, competing explanations |
| Tests, operational checks, rollback | Observable outcome and guardrail metrics | Discriminating observations and falsification |
| Technical dependencies | Learning and adoption dependencies | Evidence and experiment dependencies |

## Challenge and resolve

First check requirement-to-deliverable coverage, dependencies, existing contracts, source support, and diagram/prose agreement yourself. Self-checking remains useful even when independent review follows.

For standard/deep, read [review.md](review.md) and request the bounded fresh-agent review it defines when the host permits delegation. Give reviewers a compact brief and evidence pointers, not the full conversation. Keep initial judgments separate. Prefer an already available different model family for deep review when authorized; do not install a provider or incur a new paid service merely to fill a role.

If fresh reviewers are unavailable or prohibited, perform the strongest permitted check and report **self-checked; independent review unavailable** with the reason. Never role-play multiple personas and call them independent. State whether actual reviewers used the same model, different models, or unverified model identities.

Resolve material findings against sources. A changed stance needs new evidence or an identified reasoning error. Stop debate when no material dispute remains, a round brings no new evidence or corrected inference, or the mode's cap is reached. Preserve unresolved dissent with its consequence and cheapest next check; votes and agreement are not proof. User-value tradeoffs belong in the decision list, not the defect list.

## Deliver a short, inspectable artifact

Lead with the recommendation and why. Include only the following content that matters for the task; this is not a mandatory heading list:

- Goal, boundaries, success criteria, and consequential assumptions.
- Serious alternatives and the decision that separates them.
- The useful diagram and deliverables with dependencies/acceptance checks.
- Material evidence, risks, reversal conditions, and unresolved decisions.
- A verification receipt: checks actually run, review actually performed, important limits, and why the process stopped.

For a substantive plan, aim for a front page around 500–900 words; small tasks can be much shorter. Never omit a critical caveat to hit a word cap. Keep detailed evidence and settled debate behind links when they would swamp the decision. Use compact decision IDs (`D1`, `D2`) with options and your recommendation so the user can resolve them directly.

Save substantive plans and their decisions in the user-wide library using [records.md](records.md), with an outcome initially marked pending. Default to `~/.local/share/grounded-plan/`; an explicit `--store DIR` or `GROUNDED_PLAN_HOME` can override it. Honor an explicit artifact destination or request not to save. Existing plans remain at their original paths and can be referenced by a library record; do not migrate or duplicate them automatically. Maintain one canonical plan, preserve original expectations and dated decisions, and reread the record after context loss. Return the saved artifact link and record ID. If access is unavailable, report the unsaved record rather than silently storing it in the repository.

Report actual token/tool usage when available. Otherwise give work proxies, such as review calls and checks, and label them as proxies. Do not invent prices or cost savings. Review limits are instruction-level budgets, not host-enforced billing limits. Recheck changed decisions and affected evidence; don't replay the whole process for cosmetic revisions.
