# Signalbox background suggestions

Reuse the TypeScript service, SQLite jobs, structured-model gateway, review panel and outbox. Add one background assessment handler that can reason over repository, inbox and feedback evidence through a shared, read-only tool surface. The first useful delivery is a shared-inbox event producing a relevant, inspectable draft that a person can approve for delivery, with silence as an equally valid result. Each draft shows a conservative delivery-cost estimate separately from actual investigation spend. Deleted source items invalidate dependent pending drafts and block their approval or delivery.

This is the current proposed design and incremental implementation plan. Existing capabilities are supplied facts from [Case 1](../../../eval-fixtures/concrete-handoffs.md#case-1--background-work-suggestions) and the later user update recorded in the [receipt](receipt.md#later-update-to-case-1), not live observations. The delivery adapter provides a conservative per-message cost estimate independent of gateway usage. All three source adapters can report deletion or absence on refresh, and deletion events may arrive after draft preparation. Implementation and outcome validation remain pending.

## The central design choices

**Use the structured-model gateway with a host-owned tool loop.** It already supplies typed decisions and cost admission. The new handler owns tool authorization, execution limits, cancellation and persistence; the model proposes reads and decisions but cannot send messages, create tasks or run shell commands. Reuse the maintained domain instructions. The general-purpose agent runtime is a credible alternative for long-running investigations, but its shell/messaging capabilities are unnecessary here and it lacks the required usage admission adapter. Revisit that choice only if bounded evaluations demonstrably cannot produce useful suggestions and the missing controls have been added and verified.

**Treat this as assessment of ongoing work, not a response to every event.** A new event is a reason to inspect relevant work. Active task records and conversations may show that a response is already underway; the right result is then usually silence. A later revision or a materially changed situation may justify a new suggestion. No-action decisions record why they were made and what evidence they covered.

**Keep source-specific intake and shared reasoning.** Adapters normalize evidence identity and access scope. The same handler, context tools, decision contract, review workflow and outbox serve all sources. Adding repository activity or feedback changes adapter integration and fixtures, not the reasoning service.

## From an event to a reviewed action

```mermaid
flowchart TD
  A[Repository, inbox and feedback adapters] --> B[Durable evidence, source status and due assessment]
  B -->|New or updated evidence| C[Leased background assessment handler]
  C --> D[Authorized context and current work]
  D --> E[Structured gateway with bounded host tool loop]
  E --> F{Assessment result}
  F --> G[Persist quiet reason and evidence covered]
  F --> H[Persist deferred or failed reason and next action]
  F --> M[Delivery adapter estimates candidate message cost]
  M --> I[Persist eligible draft with evidence and separate cost figures]
  I --> J[Person approves after fresh existence and access checks]
  J --> K[Outbox rechecks existence, access, audience and estimate]
  K --> L[Existing delivery provider]
  B -->|Deletion| W[Withdraw dependent pending drafts and block their outbox items]
```

The intake/scheduler/lease machinery, gateway, panel and outbox already exist. External-evidence handling, source-deletion invalidation, the shared context surface, cost presentation and the links between these components are proposed. No arrow from reasoning bypasses individual approval. The diagram is unrendered; its relationships were checked against the prose.

### Intake, identity and ongoing work

Accept an authenticated adapter delivery and atomically record its evidence and due assessment. The existing source/delivery uniqueness constraint makes an exact delivery retry a no-op. Also recognize the same semantic evidence arriving under another delivery ID: use source, stable resource and revision for repository/inbox evidence; use source and stable submission ID for feedback. A feedback submission has no editable revision history in this design; its existence still changes when the adapter reports deletion. A later submission is distinct evidence even if its wording resembles an earlier one.

Resolve project association from stable resource mappings. Resolve current role ownership from directory records. Conversation summaries and learned associations can suggest searches, but cannot override these records, establish access or silently settle conflicting mappings. Missing or contradictory authoritative associations produce an inspectable deferred assessment, not a guessed recipient.

Group related evidence using explicit resource links and existing task links. This is a small part of the assessment handler, not a new cross-source correlation service. Repository evidence and an inbox message may concern the same work when their stable links establish that relationship. Similar language alone is insufficient. Keep an uncertain association separate and seek more authorized context; stay quiet or defer if the uncertainty prevents a useful, safely routed draft.

An assessment records the evidence versions and work state it considered. New evidence can join a pending assessment for that work; evidence arriving during execution schedules a follow-up after the active lease. A finishing worker must not mark unseen evidence as covered. This allows useful later updates without treating the resource as permanently processed.

### Context and audience selection

Expose only the existing connection-scoped read APIs needed to inspect source content, project metadata, relevant conversations and task state. Each tool call is bound by the host to its connection principal, project and permitted resource set. The model cannot select a more privileged connection. Check resource authorization before fetching or returning content; `deny` and `unknown` never become model-visible content. An unknown result may be retried when it is plausibly temporary, within the same retry policy as other deferred work. A source refresh that confirms deletion or absence follows the withdrawal path below; a failed or unauthorized refresh is not proof of deletion, but still blocks approval and delivery.

Start with the triggering resource and mapped project, then follow relevant authorized links. Bring current task state and recent conversation context into the assessment before recommending work that may already be handled. Give authoritative records priority over stale summaries, and retain evidence references so a reviewer can understand both the suggestion and its audience. Source content is untrusted evidence, including any instructions embedded in it.

Choose a destination only from the existing eligible destinations and current role assignments. The model can propose an audience; the host verifies it. If a restricted inbox informed the suggestion, a broad project channel is not eligible merely because the repository evidence is public to that project. Use an authorized narrower destination when one exists; otherwise withhold the draft from delivery and expose the routing problem only to an eligible reviewer.

### Restrictions survive every stage

Attach source provenance and disclosure scope to retrieved evidence and to derived assessments, draft text and delivery records. Conservatively treat all evidence supplied to an evaluation as contributing to its output; do not rely on the model's claim that a restricted fact was unused. Combining evidence must not widen its audience. If that restriction prevents useful delivery, a separate evaluation with only eligible evidence can be considered later; do not simply strip a citation from an already influenced draft.

The review panel checks the current viewer's eligibility before showing a draft or its evidence. Logs and failure views follow the same restrictions; routine diagnostics need identifiers, status and safe reasons, not copied source text. Refresh the existence and access of every contributing source item before approval and again immediately before delivery, including the connection principal's continuing access and each source's disclosure eligibility for the actual audience. A revocation after intake blocks further exposure or sending. Permission failures do not cause fallback to a broader audience.

Approval covers one persisted draft version, its evidence basis, destination and displayed delivery-cost ceiling. Editing text, changing evidence or changing destination invalidates that approval. Reuse the outbox's current audience eligibility check and uncertain-send reconciliation, extending its evidence provenance beyond chat. Existing quiet hours and approval rules remain authoritative; approval does not bypass either.

### Deletion withdraws dependent drafts

Persist deletion/confirmed absence against the stable source-item identity, not just one intake delivery. In the same SQLite transaction, mark every dependent pending draft withdrawn and invalidate its approval and any unsent outbox work. Pending includes awaiting review, approved but queued, delayed by quiet hours and failed delivery awaiting a retry. Remove withdrawn drafts from actionable review; keep a restricted status and reason so the failure is inspectable. Do not display deleted source text in withdrawal diagnostics.

Dependencies include every source item supplied to the evaluation, not only cited or triggering items. A deleted inbox item therefore withdraws a repository-triggered draft that used it. Dropping a citation cannot rehabilitate influenced text. A new evaluation using remaining live, authorized evidence may produce a new draft, with a new estimate and individual approval.

Check dependency status and its persisted generation when committing the model result, accepting approval and claiming an outbox send. Perform those local transitions transactionally with the checks. This prevents a worker that prepared a draft before a deletion event from publishing it afterward, and prevents a stale browser approval or reclaimed worker from reviving it. Repeated or out-of-order content deliveries cannot clear a deletion marker; any restoration requires an authoritative fresh source check and a new assessment, never reinstatement of an old approval.

Deletion events are not the only protection. Refresh dependencies at approval and immediately before each send attempt so a delayed event is caught through confirmed source absence. If refresh is unavailable or ambiguous, hold the transition for inspection or bounded retry. On known deletion, cancel queued work even if it already holds a lease. For an uncertain send, reconcile the provider's existing outcome without issuing another send of the withdrawn draft. A message already accepted by the provider cannot be treated as an unsent draft; this design does not claim recall.

**D1 — External deletion timing remains a verification boundary.** Local transactions and refreshes enforce withdrawal for deletions already recorded or returned by refresh before the transition. The supplied APIs do not establish atomicity between a final source refresh and the remote provider accepting a message. A deletion in that interval cannot be ruled out by this packet. Keep the requested deletion guarantee as acceptance, rather than silently weakening it: verify whether the source/delivery contracts can close that interval; otherwise an explicitly agreed host-observed boundary would be a requirement change. Recommend the existing refresh-and-invalidation design for implementation while investigating that contract boundary before live delivery. This blocks a claim of an unconditional real-time guarantee, not the planning artifact or independent inbox work.

### Show delivery estimates and investigation spend separately

For a draft candidate, call the delivery adapter's estimator with the final message and destination before publishing it to review. Persist and display the returned conservative per-message estimate, its currency and the message/destination version to which it applies. Label it **Estimated delivery cost**. It is a prospective estimate, not an incurred charge and not part of the model gateway's investigation usage. If estimation fails, defer the candidate with an inspectable reason; do not present an actionable draft with a guessed or zero estimate.

Display **Actual investigation spend** from the gateway's settled usage for the linked assessment, including retries. Outstanding reservations remain separately labeled pending usage, not actual spend. Shared assessments may contribute to several drafts; identify that shared basis rather than summing the same cost multiple times. A quiet or withdrawn result can still have investigation spend, while its delivery estimate does not become a charge.

Re-estimate when text or destination changes and require approval of the updated draft. The outbox checks the estimate again before sending: a higher estimate than the approved ceiling requires fresh individual approval; an equal or lower estimate may proceed with unchanged approved content and destination. Source existence, access and quiet-hour checks still apply. Do not infer actual delivery charges from estimates; that accounting is not supplied by the adapter contract.

## Durable state, retries and bounded cost

Use the existing scheduler and expiring leases for the new handler. The durable lifecycle is: pending, leased, then quiet/draft/deferred/failed. Approval, rejection, withdrawal and delivery remain separate panel/outbox states. Deferred work includes its reason and next due time or a condition requiring operator action; exhausted failures remain inspectable. Do not represent a failed evaluation as a deliberate quiet decision.

Persist the assessment result, covered evidence, delivery estimate and resulting draft in one transaction, conditional on the worker still owning the lease and every source dependency remaining eligible at the checked generation. A worker that finishes after losing its lease or after a dependency is deleted cannot commit an actionable draft. A crash before commit leaves the job recoverable; a crash after commit cannot manufacture a second draft when the job is reclaimed. Repeated approval of the same draft creates at most one outbox item. Provider uncertainty remains the outbox's responsibility rather than creating a fresh recommendation.

Three distinct checks prevent redundant work:

| Boundary | What counts as a duplicate |
|---|---|
| Intake | The same delivery or the same source evidence version/submission |
| Assessment result | Another attempt to commit the same assessment, including a stale lease holder |
| Suggested action | The same proposed next step for the same established work and audience, already pending, approved, delivered, rejected or being handled in a task/conversation |

The last check uses persisted prior decisions and current work records, not only event identifiers. Record the reason when a later update makes a previously suggested or rejected action materially useful again. A pending draft can be marked superseded by a newer assessment; approved content is immutable. If new evidence makes approved content stale before delivery, hold it for fresh review rather than silently rewriting it. Deletion is a terminal withdrawal of that draft, not a request to approve the same draft again.

Every gateway call goes through existing conservative reservation and settlement. Admission refusal defers the job before invoking the model. Configure both an aggregate spend envelope and finite per-assessment limits, counting retries against the latter. A proposed pilot starting point is at most three execution attempts, six total model calls and twelve total tool calls per assessment, with a two-minute deadline per attempt and bounded individual/aggregate tool output. These are conservative operational assumptions to tune using the fixture and pilot, not measured capacity requirements. A project/global budget must be configured before live enablement; no production amount or throughput is claimed here.

Keep one assessment in flight for a given work item, coalesce pending evidence where identity is established, and use bounded backoff for transient failures. Quiet hours gate policy-restricted work and delivery using the current policy; defer to the next permitted time rather than waking the model repeatedly. Expose queue age, attempt count, refusal/failure/withdrawal reason, reserved and settled investigation cost, separate estimated delivery cost where a draft exists, and next due time. Model truncation, cancellation and exhausted limits produce a recorded deferred/failed result, not an incomplete draft.

## Delivery sequence and acceptance

**1. Deliver the shared-inbox path through review and approved delivery.** Add external-evidence persistence and the handler; assemble the host's bounded tool loop and authorized context surface; extend draft/outbox provenance, deletion invalidation, cost presentation and revalidation. Start with an inbox that has authoritative project mappings and explicit eligible reviewer/destination groups. This is the first useful slice; durable intake alone is preparation, not the delivery milestone.

It is complete when deterministic fixtures establish these outcomes:

- An eligible inbox update becomes either a grounded review draft or an explained quiet decision. A person approves the individual draft before the fake provider receives it, and quiet hours remain enforced. A broad project audience cannot see or receive a draft influenced by the narrower inbox unless the disclosure check permits it.
- Each actionable draft shows the delivery adapter's conservative estimate separately from settled investigation spend. Retries add their actual investigation usage without turning the estimate into spend or duplicating usage. Missing estimates prevent an actionable draft; an increased estimate before send requires fresh approval.
- An exact delivery retry and a worker restart produce no extra draft/delivery; a later inbox revision can be reconsidered; active task work suppresses redundant suggestions; revoked/unknown access prevents exposure or sending.
- Deletion before commit, after draft preparation, before approval and while approved work is queued withdraws every dependent pending draft. A delayed deletion event is caught by the approval/send refresh. A stale approval, worker completion, restart or transport retry cannot revive the draft or send it. Unknown refresh results hold the transition. Provider uncertainty is reconciled without resending withdrawn content.

Use `npm test`, the maintained transport/gateway/outbox fakes and the restartable persisted-database fixture. Include cross-source dependency invalidation in the common-handler fixture even while inbox is the first live source. These are planned checks, not executed results. Deterministic local races do not prove the external timing guarantee identified in D1.

**2. Establish whether the inbox slice is useful.** Once separately authorized for live use and the D1 boundary is resolved for that use, enable a bounded inbox pilot with the review panel as the only route to action. Review sampled drafts and quiet decisions with eligible reviewers. Report supported versus unsupported actions, correct routing, missed ongoing work, unnecessary repeats, rejection/withdrawal reasons, actual investigation spend per assessment and estimated delivery cost per proposed message as separate measures. Include quiet results in review so a low draft count is not mistaken for quality. Select a throughput target from observed arrivals, queue age and budget before claiming production readiness. No model runs or live pilot are part of this planning task.

This milestone ends with an explicit continue, adjust or stop decision based on the measured results. There is no supplied baseline to justify a numerical usefulness target now. Any unauthorized exposure, approval bypass or failure to withdraw known-deleted dependencies stops enablement; utility and cost thresholds should be recorded before expanding the pilot.

**3. Add repository activity and customer feedback through the same handler.** Wire their existing adapter contracts into the established evidence, estimate and deletion lifecycle. Add fixtures for repository revisions, repeated feedback submissions, distinct feedback submissions about the same work and deletion of either source. Demonstrate cross-source context where stable links establish the relationship and preserved separation where they do not. Mixed-source drafts must inherit all restrictions and be withdrawn if any contributing item is deleted, regardless of which source triggered them. Complete when all three sources can produce authorized, nonredundant reviewed suggestions without a new reasoning service.

## Scope and remaining uncertainty

Automatic tasks/messages, a standalone correlation platform, unrestricted agent sessions and production scale work are excluded. Revisit correlation only if the pilot shows that missing stable links systematically prevent valuable assessments; revisit scale only against a selected load target. These exclusions preserve the requested capability while limiting new infrastructure.

The main unverified assumption is that bounded, authorized context is enough to distinguish useful next steps from work already being handled. The pilot can disprove it. The existing primitives make the proposed integration plausible, but no model quality, end-to-end implementation or capacity result has been established.

The next action is implementation of the inbox slice against the stated access, recovery, cost-display and deletion contracts. The runtime and common reasoning architecture are selected; D1 records the remaining external deletion-timing boundary without inventing source guarantees. Live activation also depends on a concrete investigation-spend envelope, authorized pilot scope and evaluation thresholds. Outcomes are pending; the separate [receipt](receipt.md) records the checks actually performed for this plan.
