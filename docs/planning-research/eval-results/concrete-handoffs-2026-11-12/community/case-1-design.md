# Background work suggestions — proposed system design

Status: proposal for review, not an accepted design or implementation authorization. The supplied case 1 packet is the complete factual source; all new contracts, paths, limits and behavior below are proposed engineering decisions.

## Intent and success

Signalbox should consider new repository activity, shared-inbox messages and customer feedback together with ongoing work, then either prepare a useful next step for a person to review or stay quiet. The first delivery must demonstrate the complete repository → evidence → bounded evaluation → review → individually approved delivery flow. An intake-only milestone does not meet that goal.

Success means a relevant repository update can produce an evidence-backed draft for an authorized reviewer; irrelevant or already-handled work produces no draft; exact retries produce neither duplicate evaluation work nor duplicate drafts; a genuinely new revision can produce a useful later suggestion; and crashes, budget refusal and authorization changes leave an inspectable outcome. Use deterministic local fixtures first. No claim about production throughput, model quality or user benefit is justified yet.

Non-goals are autonomous task creation, automatic messages, shell access, a new agent platform, a comprehensive cross-source knowledge graph, source setup, or replacing existing scheduling, approval and delivery systems. Anti-goals include leaking restricted inbox context into project-channel suggestions, presenting stale hints as ownership facts, and shipping a durable queue that has no useful reviewed output.

## Known foundation and constraints

The existing TypeScript/SQLite service has atomic evidence/job/decision transactions, a scheduler polling every ten seconds, leased workers with attempts and next-due times, and chat-thread handlers. External evidence needs a new job handler. Authenticated adapters already supply source and delivery identity, resource identity, revision, time and a content reference. Repository and inbox revisions are stable; feedback has stable submission identity but no revision history.

The structured-model gateway already reserves a conservative ceiling before each model call and settles reported usage afterward. The caller must implement the tool loop and bounds. The alternative general-purpose runtime has sessions, shell and messaging tools but lacks a per-call admission adapter. Both can consume maintained domain instructions.

Connection-scoped read APIs, authoritative project mappings, current directory roles, linked task records, a draft review panel and a reconciling outbox already exist. They are not yet connected into this background capability. Resource authorization is allow/deny/unknown; disclosure compatibility is a separate check; both can change. Conversation summaries and learned associations are hints, not authority.

Project-wide requirements carried into the plan:

- Drafts appear in a review panel. A person approves an individual draft before existing delivery machinery sends it. No automatic tasks or external messages.
- Preserve each source's disclosure restrictions through retrieval, drafts and delivery.
- Exact source/delivery retries must not produce duplicate work or drafts; a later update about the same work may be useful.
- Avoid redundant suggestions about work already being handled.
- Start with repository activity; inbox and feedback must use the same reasoning service.
- Keep costs bounded and failed/deferred work inspectable. Current quiet-hours and approval policies remain in force.
- Implementation language and storage remain TypeScript and SQLite; use the existing scheduler, gateway, read APIs, review panel and outbox.

## Approaches

| Approach | What it changes | Tradeoff |
|---|---|---|
| **Worker-owned structured gateway loop — recommended** | Add an external-evidence handler, a restricted context/tool facade, durable decision records and review/outbox metadata. | Directly reuses admission and typed decisions. Requires explicit loop, context and authorization code, which this design specifies. |
| General-purpose agent runtime | Adapt durable external-evidence jobs into sessions; remove shell/messaging capabilities; add per-call admission, cancellation and provenance enforcement. | Sessions may help longer investigations, but add new controls and recovery state before the first useful slice. No demonstrated need justifies them here. |

The author selects the structured gateway under the user's delegation of technical choices. This is a proposal, not a recorded user approval. Per-source reasoning services are excluded: source differences belong in adapters and evidence normalization.

## End-to-end flow

```text
Authenticated source adapter
  → transaction: receipt + immutable evidence + coalesced resource job
  → leased external-evidence handler
  → current authorized context + candidate work/audience
  → cost-admitted, bounded model/tool loop
  → transaction: decision + quiet/deferred outcome OR review draft
  → reviewer sees authorized evidence and approves one exact draft version
  → durable delivery intent → existing outbox → final checks → send/reconcile
```

The review card should show: proposed next step; why now; source references and versions; related ongoing task and its current state; intended audience; and approve/reject controls. Only reviewers authorized for the entire evaluation's disclosed context may view it. A changed or invalidated draft cannot reuse an older approval. An operator who lacks evidence access sees a sanitized status such as “authorization required,” not hidden source names, snippets or draft bodies.

## Identity, durable state and update handling

Use three different identities; none substitutes for another:

1. **Delivery identity:** `(connectionId, sourceId, deliveryId)`. A receipt uniqueness constraint makes transport retries no-ops. A reused delivery ID with conflicting metadata is quarantined as an intake conflict, without overwriting the original.
2. **Evidence identity:** `(connectionId, sourceId, resourceId, versionKey)`. `versionKey` is the adapter revision for repository/inbox, and the stable submission ID for feedback. A distinct delivery of the same resource revision records its receipt but does not schedule new reasoning. Feedback must supply its stable submission identity; timestamps or content hashes are not replacement identities.
3. **Work identity:** an authoritative linked task ID when current task records identify exactly one matching task, otherwise the stable source/resource identity. Project mapping is required for routing. Ambiguous task links or project mappings defer the suggestion. Learned associations can suggest searches but cannot create a work identity or choose an owner.

Add receipt/evidence tables, a per-resource generation cursor, an evaluation table, and a small background cost-reservation ledger. Reuse existing job storage, draft storage, approval policy and outbox. Evidence stores content references and identity, not an unrestricted copy of all source text. Until source restrictions are resolved, intake rows are host-only and do not appear in reviewer/operator content views. One logical evaluation ID is unique to `(resourceKey, generation)` and is reused across attempts, so retries cannot reset call slots. Evaluation records hold input evidence IDs, generation, context digest, candidate work/audience, all consumed read dependencies, structured result/reason, call and cost accounting, attempts and timestamps. Sensitive evaluation fields inherit the context's restrictions.

Intake atomically inserts the receipt and new evidence, advances the resource generation, and schedules/coalesces one resource job. The proposed debounce is 30 seconds from the first pending event, never extended indefinitely by a busy stream. A running job captures a generation; new evidence makes the resource dirty. Its decision and draft insertion must compare that generation and the current lease fence in one transaction. If either is stale, publish no draft and leave/schedule the next generation. Store an inspectable stale-snapshot outcome.

Revisions are opaque, not sortable strings. During evaluation read the source's current resource state and revision through the connection API; retain older evidence as provenance. If the host cannot establish which mutable state is current, defer a stale-sensitive suggestion instead of guessing from delivery order or timestamps. An old revision arriving late must not roll the working context backward.

A unique active-suggestion claim on `canonicalWorkKey` permits at most one pending suggestion about the same known work, even across audiences. This conservative rule avoids parallel competing drafts; a hidden claim is checked by the host without exposing its audience or contents to an unauthorized model or reviewer. Acquire it transactionally when publishing a draft. A newer useful change may replace an unapproved draft with a new version, invalidating any stale UI approval token. Approved/pending deliveries are immutable; hold further suggestions until the outbox resolves them, then reevaluate current context. Sent, rejected and quiet evaluations remain comparison history, not permanent suppression tombstones.

For a new revision, compare current tasks, pending drafts/deliveries and the last resolved suggestion. A model proposal must identify new evidence and explain a material reason to act now. No new evidence or a matching pending action means quiet/merge, not another draft. A rejected draft is not recreated for the same evidence; a later material update can be considered. Active tasks suppress suggestions that merely recreate or ask for work already being done; they do not prohibit a distinct blocker or newly required review. Cross-source deduplication is reliable only where authoritative task/resource links connect the sources. Unlinked evidence is not silently merged on semantic similarity; this is an explicit first-version limitation.

## Context, audience and authorization

The host assembles context in this order:

1. Resolve the connection principal and reauthorize the triggering resource. Deny stops processing; unknown defers. Authentication at intake alone is insufficient.
2. Fetch current source state and source disclosure scope. Resolve project by stable resource mapping and current roles from the directory. Missing or conflicting authoritative mappings defer; stale summaries cannot fill them in.
3. Fetch current linked task records, then relevant conversation summaries and history only as permitted. Exact resource links establish current task relationships. Summaries and learned associations can rank additional searches; conflicts favor current source state, task records, mappings and directory records.
4. Compute allowed audience candidates from project policy/current roles. For each candidate, check whether every consumed source scope may be disclosed there. No compatible candidate means deferred/restricted, not a public fallback.
5. Give the model only this authorized context and host-issued candidate handles. Any additional model-requested read goes through the same facade, authorization, scope ledger and limits.

Resource access and destination disclosure are separate predicates. The host binds tools to the job's connection principal; model arguments cannot change principal or supply raw credentials. Candidate cross-source reads must have an authorized connection and a canonical resource relationship. Unavailable connections remain unavailable. Tools are read-only source content, project metadata/directory roles, conversations and task records. No arbitrary URLs, SQL, shell, task mutation or messaging tools exist in this surface.

Every successful read registers its resource/version, authorization dependency and disclosure scope before its content reaches the model. This includes task and conversation context, not just final citations. A draft's permissible audience is the intersection of all consumed scopes, including unquoted context that could have shaped the wording. The model may choose a narrower eligible audience but cannot broaden it or discard restrictions by omitting a citation. User-visible evidence links, explanations and diagnostic excerpts follow the same restrictions.

External payloads are explicitly labeled untrusted evidence. Maintained domain instructions and host controls are separate. Content telling the model to bypass review, reveal other resources or invoke tools is data. Tool arguments, returned decision schema, work handle, audience handle, citation IDs, output size and action kind are validated by the host.

At review access, approval and immediately before delivery, recheck current resource access, all consumed disclosure scopes and audience eligibility. Refresh current work state at approval and delivery: a closed task, changed audience, lost permission, or a changed relied-on source revision/work-state digest invalidates the draft and requires reevaluation and fresh approval. Never silently rewrite approved text. An external permission change after the final check and before a provider accepts a send cannot be made atomic across services; keep the check adjacent to sending and preserve the provider's own access checks.

## Bounded reasoning contract

The same evaluator consumes normalized evidence from all three source kinds. Its typed result is one of:

- `quiet`: `already_handled`, `no_material_change` or `no_useful_next_step`.
- `defer`: `missing_context` or `conflicting_context`; host failures add specific operational reasons such as unknown access, budget refusal or transient API failure.
- `draft`: a host-issued work and audience handle, a next-step kind (`request_review`, `request_status`, `report_blocker`, `suggest_follow_up`), body, supporting evidence IDs, new evidence IDs and a concise why-now explanation.

Only a message draft is delivered in the initial contract. It may recommend a task, but neither evaluation nor approval automatically creates a task. The host rejects unsupported IDs, absent novelty evidence, invalid audiences and malformed results. A quiet result is a successful outcome, not an error to retry until a draft appears.

Proposed initial limits are three model calls, eight total host content reads including initial assembly, 32 KiB total returned content, 24 KiB maximum model input per call, 4 KiB final draft body, and a 90-second evaluation deadline. The external-evidence lease is 120 seconds; fencing still controls every terminal write. Exceeding a bound records a specific deferred outcome rather than returning an unchecked partial draft. These are adjustable first-release defaults, not measured capacity or quality targets.

Each model call reserves its conservative ceiling through the existing gateway before starting and settles reported usage afterward. A job may reserve at most three such ceilings, further limited by a dedicated background daily allocation and the existing account budget. The background allocation defaults to zero until explicitly configured; no invented production price or load target is assumed. A SQLite ledger reserves from the UTC-day allocation before gateway admission, releases on admission refusal, and settles idempotently from gateway usage. Unknown outcomes retain the full ceiling. Persisted admitted-or-uncertain call slots enforce the three-call limit across worker restarts; a retry does not reset the budget. A definite gateway refusal releases its slot and local reservation; uncertain acceptance retains both until reconciled. On a crash/unknown usage, retain the conservative reservation under the gateway's existing recovery policy; do not assume cancellation made an in-flight call free. Cancellation propagates to model/tools, and late responses cannot publish after lease loss.

## Recovery, inspection and delivery

Existing worker attempt counters record all runs. Add a consecutive transient-failure count to job metadata: retry at 1 minute, 5 minutes, 30 minutes and 2 hours; after the fifth transient failure mark failed for authorized inspection/requeue. Admission refusal and unknown authorization defer for 15 minutes without consuming that failure count. Deferred work expires to an inspectable parked state after 24 hours unless the existing quiet-hours policy supplies a later eligible time. Quiet hours use that policy's own next-eligible time, not a new interpretation of time zones or allowed delivery periods. Requeue refreshes authorization and context and keeps delivery idempotency.

Persist reason codes, next due time, failure count, last attempt and budget/call usage. Authorized reviewers can inspect evidence-backed outcomes; operators get sanitized operational diagnostics. Aggregate counts cover intake retries, coalescing, quiet/draft/deferred/failed outcomes, unauthorized attempts, model usage, lease losses, approval/rejection and delivery reconciliation. Do not put source text or restricted draft content in unrestricted logs.

Approval records one immutable draft version, audience and context digest. In the same SQLite transaction, save that approval and a durable delivery job. Its outbox enqueue key is `background:<draftId>:<version>`; enqueue must be idempotent, so a crash between outbox acceptance and job acknowledgement cannot create a second send. Extend existing outbox evidence metadata and eligibility hook to carry and recheck the complete dependency/scope ledger. Preserve existing uncertain-send reconciliation against the provider. If delivery is uncertain, reconcile before retrying or evaluating a replacement; do not abandon reconciliation merely because authorization was subsequently revoked.

## Delivery sequence and evidence needed

**First useful delivery:** repository normalization, durable evaluation, authorized context, bounded gateway loop, review and approval, outbox integration, and restart/failure fixtures. Keep it disabled outside an explicit repository allowlist. The local demonstration includes one useful review request, one quiet update for already-handled work, one restricted/denied case, a materially useful later revision, and a crash after send before acknowledgement. Every case must end in a visible draft, quiet reason, deferred reason or reconciled delivery, with no unapproved send.

**Broader source coverage:** add inbox and feedback normalization/intake registrations and source-specific permissions fixtures. Exercise a restricted inbox and a repository update linked to the same task, an unlinked feedback submission, and repeated feedback submission identity. The evaluator, budget controls and decision contract remain unchanged. This extension is part of the design and plan, but is not required to call the repository slice useful.

**Qualification before production enablement:** deterministic fakes establish contracts and safety, not usefulness. After separate authorization, run a small selected repository corpus through the real model with restricted read-only tools and draft delivery disabled. Human reviewers label usefulness, redundancy, audience correctness and evidence faithfulness, alongside quiet decisions. Set a cost and load target from observed volume, run an agreed load/restart check, then decide whether to enable a limited review-only pilot. Any disclosure failure or unapproved-send path blocks enablement. No real-model run, source setup or pilot is authorized by this planning request.

Builder choices left open are routine SQL/index syntax, adapting existing API response fields into the specified ports, and locating existing composition-root/migration/panel/outbox extension files. Their actual paths and APIs were not supplied or inspected. The architectural choices, safety boundaries, identities, bounds and acceptance scenarios above are not deferred to implementation.
