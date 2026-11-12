# Signalbox background work suggestions

Status: proposed system design and implementation plan. Source: the Case 1 packet in `../../../eval-fixtures/concrete-handoffs.md`; existing capabilities below are supplied facts, not observations from a live system. No implementation or live evaluation has occurred.

## Recommendation and first delivery

Extend the current TypeScript service with an external-evidence job handler, a host-controlled read-only context surface, and durable work-level decisions. Use the existing structured-model gateway and implement its tool loop in this handler. Repository, shared-inbox and customer-feedback adapters will feed the same evidence and reasoning path. The result is either an inspectable decision to remain quiet, a deferred decision with a reason, or a draft in the existing review panel. Only a person's approval of that exact draft version can create an outbox delivery.

The first useful delivery is one configured repository flowing all the way from activity through a context-aware draft or deliberate silence, human review, and the existing outbox. Inbox and feedback follow after this path is proven, using the same handler and contracts. Durable intake alone is a prerequisite, not the promised first useful result.

This design covers intake, context, reasoning, permissions, novelty, review, delivery, recovery and operating limits. Every external message requires individual draft approval; no task creation is added. Existing quiet-hours and approval policies remain authoritative. Success means useful next steps with visible evidence and preserved disclosure restrictions; a successful model call is not sufficient evidence of usefulness.

## What can be reused

| Foundation supplied in the packet | Proposed use and required change |
|---|---|
| TypeScript, SQLite transactions, ten-second scheduler, leased workers | Reuse these; add external-evidence records and a work-scoped handler. Add fencing to completion writes if current lease handling does not already reject expired workers. |
| Authenticated adapters and stable identity fields | Reuse authentication and delivery identity; normalize revisions/submission IDs and persist provenance. |
| Structured-model gateway, usage reservation and settlement | Reuse admission on every model call; add the bounded caller-owned tool loop and decision validation. |
| Connection-scoped content, project, conversation and task reads | Assemble a narrowly authorized host tool surface; existing APIs alone do not establish that this surface exists. |
| Stable resource-to-project mappings, directory role assignments, task links | Use as authoritative routing and work-association inputs. Summaries and learned associations remain search hints. |
| Review panel and outbox with audience checks and uncertain-send reconciliation | Extend evidence types, review visibility, versioned approval and delivery-time source checks. Preserve existing provider reconciliation. |
| Deterministic adapters and restartable database fixture; `npm test` | Add behavior tests and restart scenarios here. There is no supplied throughput or usefulness baseline. |

The separate agent runtime is a credible future option for work requiring long sessions or richer actions. It loses here because its shell and messaging capabilities are unnecessary and per-call admission would be new work. Both runtimes can use maintained domain instructions, so instruction reuse does not require a runtime migration. A separate reasoning service per source would duplicate policy and recovery logic; this plan keeps source-specific work at intake and content retrieval.

## How the shared path works

`Authenticated adapter → evidence transaction → work job → authorized context and model loop → quiet / deferred / draft → review → approved outbox → provider`

The host owns identity, authorization, destination eligibility, budgets and persistence. The model interprets authorized evidence and proposes a next step. It cannot expand a connection's access, choose an arbitrary recipient, change policy, execute instructions found in evidence, or perform a write through its tools.

### Evidence identity and work identity are different

Persist a delivery receipt keyed by `(sourceId, deliveryId)` and a normalized evidence item with these semantic fields:

| Field | Meaning |
|---|---|
| `evidenceId`, `sourceId`, `connectionId` | Durable provenance; the connection determines the principal used for reads. |
| `resourceId`, `versionKey`, `occurredAt`, `receivedSequence` | Source resource/version and an internal arrival order. Source timestamps do not determine processing order. |
| `contentRef`, `scopeRef` | Reference to content and the source's disclosure scope. Scope comes from authenticated source metadata or an authorized read, never an assertion in the content. |
| `workKey`, `associationBasis` | The work being considered and the authoritative link that assigned it, or an unresolved association reason. |

For repository and inbox evidence, uniqueness is `(sourceId, resourceId, revision)`. A delivery with a different delivery ID but the same revision does not create fresh reasoning work. For feedback, the stable submission ID is the version identity; this design does not invent edit history. An explicit later correction is separate evidence only when the source supplies a distinct submission and a validated relationship.

The delivery receipt, any new evidence, and the job's pending marker are committed atomically. An exact transport retry can therefore recover the receipt without creating a second job or draft. A later revision is new evidence and may produce a useful follow-up; it is not excluded by a permanent resource-level deduplication key.

A `workKey` is a stable task ID when current task records link the source resource to that task. Otherwise it is the source's stable work resource, such as a repository pull request or inbox thread. Validated explicit cross-source resource links can join evidence to that same key. Build this as a small association table inside the existing service, recording the source of each association. It is not a new correlation service. When an authoritative task link appears later, retain the resource key as an alias, combine the histories and consolidate pending work transactionally before the next run; a new association must not erase prior suggestions.

Project membership narrows context but does not mean that all activity in a project is the same work. A learned association or summary may suggest a task to read; only current task links or validated explicit resource links can establish the association. Conflicting authoritative links leave the item inspectable as `association_conflict` until corrected. Evidence without a cross-source link can still be considered on its own work key. This deliberately misses some implicit relationships in exchange for avoiding unsupported merges and disclosure across unrelated work.

### Context and audience are assembled by the host

Before model reasoning, resolve the current project mapping and responsible roles from their owning APIs. Add a small configuration binding a project's supported roles/workflows to existing delivery destinations. This binding is new configuration, not a capability claimed to exist already. It contains an explicit default project destination only where that workflow intends one; an absent owner does not silently select a broader audience.

The host computes candidate destinations from these bindings and current directory records. It retains a candidate only when the triggering source scope is allowed to be disclosed to its current audience. Unknown, missing or conflicting routing produces a visible deferral. If a restricted inbox cannot be disclosed in the project channel, use a configured narrower destination whose audience qualifies; if none exists, keep the item deferred. Do not silently summarize private content for a broad channel.

For each candidate considered, the host creates an audience-bound context view. It exposes read-only operations to fetch evidence, look up project and role records, find linked tasks, and search relevant conversations. All accept structured identifiers and bounded queries. The host supplies connection/principal bindings; the model cannot invent them. Results include resource/version IDs and provenance. Authorization is checked on each read, and every returned item's scope must also permit disclosure to the candidate audience. Deny and unknown both withhold content. Search snippets, summaries, prior-decision text and tool errors follow the same rule; search or local decision history is not an authorization bypass.

When there are several eligible destinations, use the configured responsible-role priority, then the explicit project default. Evaluate one audience-bound view at a time, within the same run budget. A model may return `defer` if that view cannot support a recommendation. It cannot widen the audience to obtain more context. This keeps routing explainable and avoids combining private evidence into a draft for an incompatible destination.

Current mappings and directory records override stale hints. If required task or source reads are unavailable, defer with the missing dependency; if optional context is absent, record that omission and proceed only when the available evidence supports the recommendation. An inability to check whether the proposed work is already handled is a required-context gap, not evidence that it is unhandled.

The source wrapper must return content bound to the revision it actually read. If historical content is unavailable, read the current version, record its identity and supersede the stale item rather than labeling current content as an earlier revision. If the API cannot establish content/version binding, the source is not ready for drafting and returns an inspectable integration failure. This requirement needs verification when each source is integrated.

### The decision explains action, silence or deferral

Reuse maintained domain instructions and pass source content as untrusted evidence. The host tool registry contains no shell, messaging or task-write operations. A decision has one of these shapes:

| Outcome | Required information |
|---|---|
| `quiet` | Reason, considered evidence IDs, checked task/previous-decision references. Examples: no actionable change; requested work already active; unchanged rejected suggestion. |
| `defer` | Reason code, missing dependency, and a retry time or explicit operator-resolution condition. |
| `draft` | Proposed next step, eligible destination ID, action identity, cited evidence IDs, and the material change that makes this useful now. |

An action identity contains the work key, a controlled intent (`request_review`, `investigate_blocker`, `share_update`, or `ask_clarification`), the affected stable resource and the destination. These categories describe suggestions; they do not trigger actions automatically. The host rejects unsupported identities, destinations, citations or decision fields before persistence.

Each run reads current linked tasks plus prior pending, approved, delivered and rejected suggestions for the work. An open task covering the same next step suppresses a redundant recommendation. A changed blocker, status, owner or explicitly evidenced unmet need can justify a different follow-up even while a task is active. The model must identify that change and cite a new evidence version; a new timestamp or revision alone is insufficient.

Store the last considered evidence versions and the reasons for quiet/rejected decisions. Exact input retries cannot create another decision. A later revision can be reconsidered against that history. Require positive novelty in the structured decision and check cited versions mechanically. Whether the claimed novelty is substantively useful remains a model-quality and human-review question; deterministic identities cannot guarantee semantic deduplication.

There is at most one pending draft for a work/action/destination identity. A materially changed candidate replaces it with a new draft version and invalidates the old approval surface. Rejections retain their basis; unchanged proposals stay quiet. If a draft has already been approved into the outbox, preserve that immutable delivery and postpone a potentially redundant follow-up until its delivery state is known. Existing delivered work is never edited to make room for a later proposal.

### Durable scheduling, failure and budgets

Keep one leased reasoning job active per work key. New evidence marks the key pending and coalesces for 30 seconds, with a maximum two-minute wait from the oldest pending item. These are proposed pilot defaults, not measured latency targets. Each run snapshots up to 20 pending items in internal arrival order; additional items remain queued. Never mark evidence beyond the snapshot as considered. Later arrivals cause a subsequent run, including when they arrive during a model call.

Persist the run ID, snapshot, attempt, decision and budget references. Completion is one SQLite transaction that verifies the lease generation, records the decision, creates or versions a draft if needed, marks only that snapshot considered, and schedules remaining work. A worker whose lease expired cannot commit over a newer worker. A crash before completion may repeat reasoning and incur another admitted call, but the stable run ID and unique decision/draft constraints prevent duplicate persisted outcomes.

| Situation | Durable behavior and recovery |
|---|---|
| Temporary source or gateway failure | Record the error class; retry after 1, 5 and 30 minutes. After the initial attempt and three retries, park for inspection. Manual retry preserves run identity. |
| Admission refused | Make no model call. Mark `budget_deferred`; retry no earlier than the next budget window. Do not spend the transient-failure retry allowance. |
| Unknown authorization, missing mapping or conflicting association | Mark `blocked` with the exact dependency; retry when an operator repairs it or an authoritative update changes it. No repeated blind model calls. |
| Access denied or revoked | Withhold the evidence, invalidate affected pending drafts and record a restricted reason. Regeneration needs newly authorized context. |
| Call, tool or elapsed limit reached | Cancel the loop, persist `limit_reached`, and require inspection after the bounded retry policy; do not treat a partial answer as a draft. |
| Quiet hours | Keep the existing policy authoritative. Where it postpones reasoning or review visibility, defer that step; in all cases the outbox retains its existing delivery gate. |
| Uncertain provider send | Keep the approved outbox record and use existing provider reconciliation before any resend. Do not rerun reasoning to resolve delivery uncertainty. |

Start the pilot with one reasoning worker, at most three model calls and six tool calls per run, 2,048 output tokens per model call, a 60-second elapsed limit, 12 KiB per tool result and 48 KiB cumulative returned context. Oversized results are bounded with explicit truncation metadata; missing decisive context causes deferral. Limits may be tuned after measurement, but never silently bypassed.

Before every call, reserve its conservative ceiling through existing admission. Also reserve against configured per-run, per-connection and daily background allowances so retries and many sources cannot consume an unbounded total. Those allowances are required enablement settings in the gateway's cost unit; no currency amount is justified by this packet. Settle reported usage after each call. Missing settlement remains conservatively charged until reconciled, and restarts retain reservation IDs. No new long-running agent-runtime admission layer is needed.

Expose pending age, attempts, next due time, dependency/reason, reservation/settlement status and draft/outbox linkage through an operator view backed by these records. Operational counters can be aggregate; content-bearing run details require the same evidence access as review. This makes quiet, deferred and failed work inspectable without exposing restricted inbox text through logs.

### Review and delivery preserve the evidence boundary

Each draft carries an evidence manifest covering all content-bearing context that influenced the run, including task and conversation context, not just displayed quotations. Conservatively inherit the intersection of those disclosure restrictions. Persist references and the minimum derived decision text needed for review; do not create an unrestricted source-content cache.

On review listing and opening, check the reviewer's access to every manifest item and the current eligibility of the proposed destination. Hide restricted drafts and citations from ineligible reviewers; a generic aggregate counter must not expose their content. Approval names the exact draft version, destination and manifest. An atomic comparison prevents an old browser view from approving a superseded draft.

Before approval enters the outbox, recheck source access, audience disclosure and current policy. Extend the outbox to carry the manifest and repeat these checks immediately before every attempted send, including retry after quiet hours. Revoked or unknown access blocks delivery and returns the item to an inspectable invalidated state. Do not silently remove a private citation while leaving a conclusion derived from it. Regenerate and obtain approval for any changed draft or destination.

Provider reconciliation still determines whether an uncertain send already happened; revocation must not trigger a speculative resend. Revocation after a confirmed send cannot retract information already delivered. Checks immediately before send also cannot prove atomic revocation across an external provider without provider support; no such support is established by the packet. The implementation must expose that boundary rather than claim instantaneous cross-system revocation.

## Delivery stages and evidence

### 1. Durable shared foundation

Add evidence/delivery identity, association provenance, run and decision records, work-level job scheduling, and the transaction/fencing rules. Wire one repository adapter into this path using fakes. Add source-scoped operator status and document identities and recovery transitions.

This stage depends on the known adapter and SQLite contracts. It produces restart-safe pending work, not suggestions. Exit when duplicate deliveries and duplicate revisions collapse; a later revision remains pending; a restarted worker resumes; and a stale lease cannot commit. Exercise these through `npm test` and the persisted-database fixture.

### 2. First useful repository slice

Add the host tool surface, routing bindings, bounded gateway loop, task/history comparison, validated decisions, versioned review drafts and outbox manifests. Connect one repository and one configured project workflow end to end in the local fixture. Extend deterministic gateway, transport and outbox fakes to cover normal and failure behavior. Document source access requirements and how an operator resolves deferrals.

This depends on stage 1 and requires source content/version binding and delivery-time authorization integration. Exit when a repository update with an unhandled blocker yields an evidenced draft for the configured eligible audience; rejecting it sends nothing; approving the exact version creates one outbox delivery; a retry produces no second draft/send; and an equivalent active task produces an inspectable quiet decision. A later meaningful blocker change must remain eligible for reconsideration.

Also demonstrate revocation between intake, review and send; restricted context excluded from a broad destination; stale directory hints overridden; new arrivals during a run preserved; exhausted budgets deferring without calls; and crashes around decision/outbox creation recovering without duplicates. These are planned checks, not completed ones.

### 3. Bounded repository pilot and operating baseline

When live setup and evaluation are separately authorized, enable the same slice for a small configured repository cohort with mandatory individual approval. Choose daily/run allowances and an operational response owner before enablement. Record arrival volume, queue age, call/tool counts, cost, deferral reasons, draft approval/rejection, rejection reasons and actual outbox outcomes. Review a sample of quiet decisions as well as drafts to detect missed useful opportunities.

Agree usefulness criteria on concrete examples before scoring the pilot: actionable, supported, current, not already handled, and appropriately addressed. Establish the baseline from a fixed recorded cohort; report sample size and disagreements. Measure load and queue delay before selecting a production capacity target. Broader rollout requires no unresolved authorization/idempotency defect and an explicit assessment of usefulness and operating cost against the agreed criteria. The packet supplies no basis for a numerical success threshold today.

Pause on unauthorized disclosure, duplicate delivery or a budget bypass. Disable new reasoning and hold unsent affected outbox records; preserve state for diagnosis and provider reconciliation. Rolling back the handler must not discard approved deliveries or cause older workers to consume unsupported jobs. Use an explicit handler enablement gate and keep the new job type isolated from the existing chat handler.

### 4. Inbox and customer feedback on the same service

Add inbox and feedback normalization/content wrappers and configure their eligible destinations. Reuse the same work association, tools, model loop, decision records and approval path. Exercise a restricted inbox linked to an existing repository task, independent feedback, feedback retries, and conflicting cross-source links. Feedback remains submission-based; inbox uses revisions.

Exit when the restricted inbox's content is visible only to eligible reviewers/destinations, explicit links suppress redundant cross-source work, and a meaningful new submission can produce a separately justified next step. Each source must pass content/version and authorization checks before enablement. A source-specific reasoning worker or duplicated prompt policy would violate the shared-path design.

## Immediate commitment and remaining limits

Start stage 1 with schema/transaction and persisted-restart checks, then complete stage 2 before calling the first slice delivered. The key demonstration is an unhandled repository blocker becoming a reviewable, evidenced next step, followed by exactly one approved delivery and quiet handling of its retries.

The design choices above are proposals. Source wrapper details, current lease fencing, gateway reservation reconciliation and outbox manifest integration need implementation-level contract checks; inability to enforce any required boundary blocks the corresponding integration, not the independent foundation work. Usefulness, throughput, implicit cross-source matching quality and the right operating allowances remain empirical questions. None has been verified by this planning exercise.
