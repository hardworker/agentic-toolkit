# Background Work Suggestions Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a reusable background evaluator that turns new external evidence and current work context into an authorized review draft or an explicit quiet/deferred outcome, beginning with a complete shared-inbox slice, with delivery estimates and source-deletion withdrawal.

**Architecture:** Add an external-evidence job handler to the existing TypeScript/SQLite service and run a bounded, host-mediated tool loop through the structured-model gateway. Reuse the scheduler, leased workers, maintained domain instructions, connection-scoped reads, review panel and reconciling outbox. Repository activity and feedback later enter the same evaluator through normalization adapters.

**Tech Stack:** TypeScript, SQLite, existing structured-model gateway, existing deterministic adapter fakes, `npm test`; no new runtime or infrastructure dependency.

**Spec:** [Proposed system design](case-1-revised-design.md). Read it with this plan.

**Status:** Proposed engineering choices, not approved implementation. The execution-subskill notice above is preserved from the authoring method; this planning pass invokes neither execution skill, performs no implementation and requests no execution-method choice. Technical choices were delegated; the later user update sets inbox-first delivery, visible delivery estimates and deletion withdrawal. Design approval was not implied.

## Global Constraints

- Drafts appear in a review panel. A person approves an individual draft before existing delivery machinery sends it. No automatic tasks or external messages.
- Preserve each source's disclosure restrictions through retrieval, drafts and delivery.
- Exact source/delivery retries must not produce duplicate work or drafts; a later update about the same work may be useful.
- Avoid redundant suggestions about work already being handled.
- Start with shared-inbox activity; repository activity and customer feedback must use the same reasoning service.
- Every draft must show its estimated delivery cost separately from actual investigation spend.
- If a source item is deleted, pending drafts based on it must be withdrawn before approval or sending.
- Keep costs bounded and failed/deferred work inspectable. Current quiet-hours and approval policies remain in force.
- Implementation language and storage remain TypeScript and SQLite; use the existing scheduler, gateway, read APIs, review panel and outbox.

## Review Focus

These implied failure modes are explicitly added to the owning task's tests below:

1. Deletion after evaluation or approval, including unquoted source context, must withdraw affected pending drafts and prevent dispatch — Tasks 4 and 5.
2. A missing or changed delivery estimate must not be hidden by investigation spend or reused approval — Tasks 4 and 5.
3. Late inbox revisions and stale owner hints must not override current source/mapping/directory/task state — Task 2.
4. Two resources linked to the same task, or an update during a leased evaluation, must not publish competing/stale drafts — Task 4.
5. A process crash after provider acceptance but before acknowledgement must reconcile to one send, even if a deletion then arrives — Task 6.

---

## File map and integration boundaries

All paths below are proposed additions, not claims about an inspected repository. Locate the actual composition root, migration registration, review handlers and outbox eligibility extension at implementation time; their existing filenames and line numbers were not supplied. Integrate the named contracts below at those four seams and retain existing conventions. No repository reorganization is planned.

| Proposed file | Responsibility |
|---|---|
| `src/background/contracts.ts` | Normalized evidence, dependencies, decision and job types shared by tasks |
| `src/background/001-background.sql` | Receipt/evidence/presence-cursor/evaluation, dependency index, suggestion-claim and reservation schema; reuse jobs/drafts/outbox |
| `src/background/store.ts` | Atomic intake/deletion observations, withdrawal, generation fencing, publication and inspection queries |
| `src/background/context.ts` | Current context, authority rules, work/audience resolution and restricted read facade |
| `src/background/evaluate.ts` | Maintained instructions, typed decision validation and bounded model/tool loop |
| `src/background/budget.ts` | Durable background quota/call reservations layered around gateway admission |
| `src/background/review.ts` | Authorized review, immutable version approval/rejection and delivery intent |
| `src/background/delivery.ts` | Delivery estimates plus outbox evidence adapter, final presence/cost/access checks and idempotent enqueue |
| `src/background/register.ts` | Shared-inbox intake/deletion/job registration and mapping existing service adapters into ports |
| `tests/background/fixture.ts` | Temporary SQLite and deterministic fake adapters; restart against the same DB |
| `tests/background/{intake,context,evaluate,lifecycle,delivery,inbox,sources}.test.ts` | Focused contract and integration checks |
| `docs/background-suggestions.md` | Operator states, limits, review behavior, verification and enablement criteria |

The production `BackgroundPorts` type is an adapter boundary to the existing scheduler, gateway, source reads, project/directory/task/conversation reads, policy and outbox; it does not introduce implementations of those services. Every tool read returns a `ReadDependency` containing connection/source/resource identity, revision where available, disclosure-scope reference and the captured source-presence generation. The delivery estimator is an existing adapter port separate from gateway accounting. Existing SDK/model types should be imported rather than redefined.

The test fixture exports `createFixture(): Promise<BackgroundFixture>` and `inbox(overrides?: Partial<EvidenceEnvelope>): EvidenceEnvelope`. Its default inbox envelope is connection `c1`, source `inbox`, resource `thread-7`, revision `m1`, delivery `d1`, content reference `ref:thread-7:m1`, at a fixed fake clock. `BackgroundFixture` exposes `db`, `ports`, `lease`, `input`, `clock`, `state()` and `restart()`. `state()` queries counts, decisions, draft versions, job statuses/due times and reservation totals from persisted state. Fake controls used below are added alongside their owning task: `source.current`, `source.presence`, `source.access`, `directory.roles`, `tasks.records`, `gateway.decisions`, `gateway.calls`, `deliveryEstimator.estimates`, `outbox.accepted`, `outbox.uncertain`, and named fault barriers. They wrap supplied deterministic fakes; these are proposed test APIs, not asserted existing APIs.

## Task 1: Durable intake, source presence and evidence identity

**Files:** Create `contracts.ts`, `001-background.sql`, `store.ts`, `tests/background/fixture.ts` and `tests/background/intake.test.ts` at the paths above. Register the SQL with the existing migration mechanism.

**Interfaces:**

- `EvidenceEnvelope = { connectionId: string; sourceKind: 'repository' | 'inbox' | 'feedback'; sourceId: string; deliveryId: string; resourceId: string; revision: string | null; submissionId?: string; occurredAt: string; contentRef: string }`. The host supplies `connectionId`; feedback must include its stable `submissionId`.
- `ingestEvidence(db: BackgroundDb, envelope: EvidenceEnvelope, now: Date): Promise<IngestResult>`, where `IngestResult.kind` is `new_evidence | duplicate_delivery | duplicate_revision | intake_conflict` and includes `evidenceId` when applicable. `BackgroundDb` wraps the existing SQLite connection/transaction API.
- `DeletionObservation = { connectionId: string; sourceId: string; resourceId: string; deliveryId?: string; observedAt: string; reason: 'deleted' | 'absent' }`; `recordSourceDeletion(db: BackgroundDb, observation: DeletionObservation): Promise<DeletionResult>`. `DeletionResult` includes `presenceGeneration`, `withdrawnDraftIds` and `blockedDeliveryIds`; Task 4 fills the withdrawal path once drafts exist.
- `EvaluationInput = { resourceKey: string; generation: number; evidenceIds: string[] }`; `JobLease = { jobId: string; fence: string; expiresAt: Date }`. The scheduler constructs these from existing persisted job data.

- [ ] **Step 1: Write `deduplicates_delivery_but_accepts_new_revision` and transaction-failure tests.** Assert the following sequence, then separately inject a failure before transaction commit and assert zero receipt/evidence/job writes. Also test a new delivery of `m1`, a conflicting reuse of `d1`, and repeated deletion observations. A deletion without a delivery ID must still persist a tombstone; a late upsert must not clear it.

```ts
const f = await createFixture();
expect((await ingestEvidence(f.db, inbox(), f.clock.now())).kind).toBe('new_evidence');
expect((await ingestEvidence(f.db, inbox(), f.clock.now())).kind).toBe('duplicate_delivery');
expect((await ingestEvidence(f.db, inbox({ deliveryId: 'd2', revision: 'm2' }), f.clock.now())).kind).toBe('new_evidence');
expect(await f.state()).toMatchObject({ receipts: 2, evidence: 2, resourceJobs: 1, generation: 2 });
```

- [ ] **Step 2: Run `npm test -- tests/background/intake.test.ts`.** Expect failure from missing background intake/schema or unmet assertions. If the repository test runner does not accept file arguments, use `npm test` and confirm these named tests fail.
- [ ] **Step 3: Implement `ingestEvidence` and its schema.** Use the spec's distinct delivery/evidence uniqueness keys, immutable receipt linkage, atomic generation increment and one resource job. Persist source status/presence generations and a dependency index. Process deletion observations immediately without debounce or model admission; do not clear a tombstone on an incoming upsert. Set the first due time to intake + 30 seconds; later intake must not indefinitely extend it. Create the evaluation, active-work claim and cost-ledger tables needed by later tasks in the same migration. Make the logical evaluation ID unique to `(resourceKey, generation)` and reuse it across attempts; pending unclassified intake is host-only. Reject invalid identity fields without storing source content in logs.
- [ ] **Step 4: Run the intake tests.** Expect all to pass, including the conflicting-payload and rollback cases; inspect that retrying rolled-back intake creates exactly one evidence row and one job.
- [ ] **Step 5: Commit the completed intake/schema/test change locally.** Suggested message: `feat: persist external evidence and coalesced background jobs`.

## Task 2: Authorized context and authoritative work routing

**Files:** Create `context.ts`, `tests/background/context.test.ts`; extend `contracts.ts` and the test fixture.

**Interfaces:**

- `ReadDependency = { connectionId: string; sourceId: string; resourceId: string; revision: string | null; scopeRef: string; presenceGeneration: number | null }`. External source-item dependencies require a generation; non-source metadata reads use null.
- `SourceReference = { connectionId: string; sourceId: string; resourceId: string }`; `refreshSourcePresence(source: SourceReference, ports: BackgroundPorts): Promise<PresenceResult>`, where `PresenceResult` contains `kind: 'present' | 'deleted' | 'unknown' | 'raced'` and the local `generation`. Capture generation before the live read and commit a present/restored result only if unchanged; a deletion observed during the read wins.
- `ContextSnapshot = { workKey: string; audiences: AudienceHandle[]; evidenceIds: string[]; newEvidenceIds: string[]; dependencies: ReadDependency[]; resourceRevisions: Record<string, string | null>; digest: string; modelContext: string }`. `AudienceHandle = { id: string }` is host-issued; directory/policy metadata stays host-side.
- `assembleContext(input: EvaluationInput, ports: BackgroundPorts, signal: AbortSignal): Promise<ContextResult>`, where `ContextResult` is `{kind:'ready'; snapshot:ContextSnapshot}` or `{kind:'defer'|'denied'|'withdrawn'; reason:string}`.
- `readBackgroundTool(request: BackgroundReadRequest, session: ContextSession): Promise<AuthorizedReadResult>` shares the same authorization, dependency ledger, eight-read/32-KiB bounds and principal. `ContextSession` owns the input, ports, counters and collected dependencies. `BackgroundReadRequest` is a discriminated union of source/project/conversation/task reads with host-issued handles; `AuthorizedReadResult` contains authorized bounded content or a sanitized denial/defer reason. No raw connection override is accepted.

- [ ] **Step 1: Write `uses_current_revision_and_authority`, `fails_closed_on_unknown`, `tracks_unquoted_context`, and `absence_records_deletion`.** Fixture: deliver `m2`, then late `m1`; source says current `m2`; summary suggests Alice, current directory says Bob; task `t7` links `thread-7`. Assert:

```ts
const result = await assembleContext(f.input, f.ports, new AbortController().signal);
expect(result.kind).toBe('ready');
if (result.kind !== 'ready') throw new Error(result.reason);
expect(result.snapshot.workKey).toBe('task:t7');
expect(result.snapshot.resourceRevisions['thread-7']).toBe('m2');
expect(result.snapshot.audiences).toEqual([{ id: 'reviewers-for-bob' }]);
expect(result.snapshot.dependencies.map(d => d.resourceId)).toContain('conversation-9');
```

The fixture's host-issued audience `reviewers-for-bob` must come from current policy/roles. Also assert unknown access returns `defer` without a source-content read; ambiguous task/project mapping defers; a restricted conversation cannot authorize the project-channel audience; a tool request that changes the principal is rejected. No-current-revision evidence must defer stale-sensitive work. An adapter refresh reporting absence records the same tombstone as a deletion event, yields no model content and stops draft evaluation. A read error/unknown access must not be mislabeled deleted. Cached content cannot satisfy a presence refresh. In `deletion_during_presence_refresh_wins`, pause a present-state read, record deletion, then release it; assert `raced`, a retained tombstone and no draft.

- [ ] **Step 2: Run `npm test -- tests/background/context.test.ts`.** Expect the named assertions to fail before implementation.
- [ ] **Step 3: Implement the two context functions.** Implement `refreshSourcePresence` and use it for external dependencies. Refresh current source presence and its local generation; stop on deletion/absence. Read current source state, stable mapping/current directory, current linked tasks, then permitted hints/history. Use exact task resource links for canonical work identity. Maintain all consumed scopes and validate audience intersection; do not let citations reduce that ledger. Assemble initial reads and later tool reads through one counter/authorization path. Tool content is explicitly labeled untrusted evidence.
- [ ] **Step 4: Rerun the context tests.** Expect pass, with no denied-content call and no fallback routing from stale/conflicting hints.
- [ ] **Step 5: Commit locally.** Suggested message: `feat: assemble authorized background work context`.

## Task 3: Cost-admitted bounded decisions

**Files:** Create `evaluate.ts`, `budget.ts`, `tests/background/evaluate.test.ts`; extend contracts and fake gateway controls.

**Interfaces:**

- `CostAmount = { amount: string; unit: string }`; `InvestigationAccounting = { actual: CostAmount | null; pendingHeld: CostAmount | null; complete: boolean }`. Actual contains only reported settled gateway usage; held ceilings stay separate and completeness is false while any call is unresolved.
- `BackgroundDecision` is the spec's `quiet`, `defer` or `draft` union. A draft has `workKey`, `audienceId`, `nextStepKind`, `body`, `supportingEvidenceIds`, `newEvidenceIds`, `whyNow`. `nextStepKind` is exactly `request_review | request_status | report_blocker | suggest_follow_up`.
- `evaluateBackground(input: EvaluationInput, lease: JobLease, ports: BackgroundPorts, signal: AbortSignal): Promise<EvaluationOutcome>`. `EvaluationOutcome` includes a decision or operational reason, snapshot when obtained, persisted call/reservation IDs and usage; it does not publish a draft or send anything.
- `reserveBackgroundCall(db: BackgroundDb, evaluationId: string, ceilingUnits: bigint, now: Date): Promise<ReservationResult>`; `settleBackgroundCall(db: BackgroundDb, reservationId: string, actualUnits: bigint | null): Promise<void>`. `ReservationResult` is admitted with ID/ordinal or refused with reason. Null usage retains the ceiling. Gateway admission still runs after local reservation.

- [ ] **Step 1: Write tests for admission refusal, limits, hostile evidence and crash-safe accounting.** For `refusal_calls_no_model`, seed exhausted background allocation and assert zero gateway calls plus deferred reason `budget`. For `settles_once`, reserve 10 units in a 20-unit test allocation, settle 4 twice, and assert 4 charged and 16 available. For `retains_unknown_cost_across_restart`, leave usage unknown, restart, and assert all 10 units remain held with actual spend unknown/incomplete, not falsely reported as zero or 10.

```ts
const outcome = await evaluateBackground(f.input, f.lease, f.ports, new AbortController().signal);
expect(outcome.reason).toBe('budget');
expect(f.ports.gateway.calls).toHaveLength(0);
expect((await f.state()).drafts).toBe(0);
```

Table-driven cases must enforce three model calls across retries, eight total initial/tool reads, 32 KiB tool content, 24 KiB model input, 4 KiB body and a 90-second deadline. A request for a ninth read, a forged audience, an unknown evidence ID, and source text requesting a shell/send tool must yield no draft. Simulate repeated definite gateway refusals after local reserve and assert release of both reservation and call slot; a later admitted call must still be allowed. Simulate crash after accepted admission and assert conservative retention of reservation and slot.

- [ ] **Step 2: Run `npm test -- tests/background/evaluate.test.ts`.** Expect failures for the missing evaluator/ledger behavior.
- [ ] **Step 3: Implement evaluation and reservation functions.** Use the existing maintained instructions and structured gateway. Run tools sequentially through Task 2's facade, validate the typed result, and enforce cancellation and limits in host code. Atomically reserve UTC-day quota/call slot before gateway admission, release slots only on definite refusal, settle idempotently, and keep uncertain reservations/slots. Default background daily allocation to zero; a configured job may spend at most three existing per-call ceilings within available daily/account budgets. Never reset call counts on a retry.
- [ ] **Step 4: Rerun evaluator tests.** Expect all pass; every refused/over-limit/malformed run has an inspectable reason and no delivery effect. No model network calls occur in this check.
- [ ] **Step 5: Commit locally.** Suggested message: `feat: evaluate background evidence within durable cost limits`.

## Task 4: Costed publication, deletion withdrawal and recovery

**Files:** Extend `store.ts`; create the estimator adapter in `delivery.ts` and `tests/background/lifecycle.test.ts`; extend persisted-state/fault-barrier fixture support.

**Interfaces:**

- `publishEvaluation(db: BackgroundDb, input: EvaluationInput, lease: JobLease, outcome: EvaluationOutcome, costs: PreparedDraftCosts | null, now: Date): Promise<PublishResult>` where `PublishResult.kind` is `draft | quiet | deferred | stale | withdrawn | lease_lost` and carries a draft ID/version when applicable.
- `DeliveryEstimate = CostAmount & { estimatedAt: string; inputDigest: string }`; `PreparedDraftCosts = { deliveryEstimate: DeliveryEstimate; investigation: InvestigationAccounting }`. `estimateBackgroundDelivery(outcome: EvaluationOutcome, ports: BackgroundPorts): Promise<EstimateResult>` returns `{kind:'ready'; estimate:DeliveryEstimate}` or `{kind:'deferred'; reason:'delivery_estimate_unavailable'}`. Only draft decisions invoke it.
- `scheduleBackgroundOutcome(db: BackgroundDb, lease: JobLease, reason: string, now: Date): Promise<void>` applies retry/defer/park policy using existing job attempts/next-due fields and explicit transient-failure metadata.
- A persisted `ReviewDraft` contains `id`, integer `version`, `workKey`, `audienceId`, immutable body, evidence IDs, dependency ledger, context digest, source-presence generations, `deliveryEstimate`, `investigation` and review state. `withdrawn` is a terminal state for that draft version; restored sources require a new evaluation/version. Existing panel storage gains these fields/reference links; it is not replaced.

- [ ] **Step 1: Write `new_generation_invalidates_inflight_publication`, `one_pending_draft_per_work`, and novelty/recovery tests.** Pause the first evaluation before publication; ingest `m2`; resume and assert:

```ts
expect((await publishEvaluation(f.db, oldInput, oldLease, oldOutcome, oldCosts, f.clock.now())).kind).toBe('stale');
expect(await f.state()).toMatchObject({ drafts: 0, generation: 2, resourceJobs: 1 });
```

Race two resources linked to `task:t7` and assert one active draft, including when candidate audiences differ. Assert the hidden competing claim's details never enter model context. Same-evidence retries and a rejected version yield no new draft; a new material revision may produce a new version. An already-active matching task action is quiet; a distinct new blocker can be drafted. New events during an approved pending delivery wait for reconciliation. Lost lease publication must write no draft. A deletion observed after preparation but before publication must return `withdrawn`, even if it affects supplementary unquoted source context rather than the triggering item.

For `estimate_is_distinct_from_actual_spend`, have the gateway report actual investigation cost `0.07 USD` and the delivery adapter estimate `0.02 USD`; publish and assert these remain separate stored/displayable fields. An unavailable estimate creates no draft and records `delivery_estimate_unavailable`; retrying estimation with unchanged context must not add a model call. An unresolved model reservation is labeled held/incomplete, not actual spend. With a fully settled fixture, assert:

```ts
expect((await f.state()).draftCosts).toMatchObject({
  deliveryEstimate: { amount: '0.02', unit: 'USD' },
  investigation: { actual: { amount: '0.07', unit: 'USD' }, pendingHeld: null, complete: true }
});
```

For `deletion_withdraws_pending_drafts_atomically`, create both a review-pending draft and an approved-not-dispatched fixture, observe deletion, and assert both versions are withdrawn, approval tokens invalidated and pending delivery intents blocked in the same transaction. The presence generation must fence any racing publisher/approver. Repeat the observation and assert no new model job or duplicate withdrawal. A late upsert must not revive either draft; a fresh authorized present-state read may schedule a new evaluation, with fresh approval required. In a fixture with two dependent pending versions for separate work keys, assert:

```ts
const removed = await recordSourceDeletion(f.db, {
  connectionId: 'c1', sourceId: 'inbox', resourceId: 'thread-7',
  deliveryId: 'delete-1', observedAt: f.clock.now().toISOString(), reason: 'deleted'
});
expect(removed.withdrawnDraftIds.sort()).toEqual([pendingId, approvedId].sort());
expect(await f.state()).toMatchObject({ activeApprovals: 0, pendingDeliveries: 0 });
```

Add fake-clock assertions for transient retry delays of 1 minute, 5 minutes, 30 minutes and 2 hours, failure on the fifth error, budget/unknown-access deferral of 15 minutes without increasing transient failures, and parked state after 24 hours of unresolved deferral. Existing quiet-hours eligibility overrides the due time as specified; test its later next-eligible time directly.

- [ ] **Step 2: Run `npm test -- tests/background/lifecycle.test.ts`.** Expect missing publication/claim/recovery behavior to fail.
- [ ] **Step 3: Implement the publication transaction and scheduling policy.** Call the delivery estimator for validated draft text/destination and persist its estimate separately from actual/held investigation accounting. Defer publication on estimate failure without rerunning the model. Check resource generation, every source-presence generation/tombstone and lease fence; record every decision; claim canonical work atomically; compare active tasks and draft/delivery history; create or replace only unapproved draft versions. Preserve sent/rejected history for material-new-evidence comparison. Persist quiet as successful completion and failed/deferred reasons for authorized inspection. Extend `recordSourceDeletion` to atomically withdraw all dependent pending drafts and cancel/block their delivery intents, including unquoted dependencies. Requeue refreshes presence/context and never deletes existing outbox idempotency state.
- [ ] **Step 4: Rerun lifecycle tests.** Expect pass, including both orders of the parallel publication race and all fake-clock states.
- [ ] **Step 5: Commit locally.** Suggested message: `feat: publish costed background drafts and withdraw deleted sources`.

## Task 5: Individual review and existing outbox delivery

**Files:** Create `review.ts` and `tests/background/delivery.test.ts`; extend `delivery.ts`; extend the existing review handlers and outbox evidence/eligibility seam at their discovered paths.

**Interfaces:**

- `loadBackgroundDraft(draftId: string, actorId: string, ports: BackgroundPorts): Promise<ReviewAccessResult>` returns an authorized review card (with separate delivery estimate and investigation accounting), a withdrawn status or a sanitized denied result. Derive actual/held investigation amounts from current ledger settlement state, not a stale publication snapshot.
- `approveBackgroundDraft(draftId: string, version: number, actorId: string, ports: BackgroundPorts): Promise<ApprovalResult>` returns `approved | stale | denied | deferred | withdrawn | estimate_changed` and persists an immutable approval plus durable delivery job atomically.
- `rejectBackgroundDraft(draftId: string, version: number, actorId: string, ports: BackgroundPorts): Promise<void>` records a version-specific rejection after authorization.
- `enqueueBackgroundDelivery(draftId: string, version: number, ports: BackgroundPorts): Promise<DeliveryResult>` returns `queued | already_queued | invalidated | deferred | withdrawn | requires_approval`; the outbox uses key `background:<draftId>:<version>`. The existing send-boundary eligibility hook rechecks source presence, every dependency, current work state and the delivery estimate. Approval binds the displayed estimate amount/unit/input digest and the draft version; a new timestamp alone is not a price change.

- [ ] **Step 1: Write `requires_current_individual_approval` and revocation/change tests.** Seed a draft consuming restricted inbox evidence plus unquoted source context. Before approval assert zero outbox entries. Approve as an authorized reviewer and assert one entry with its exact version; repeat and assert no second entry. Then revoke the conversation before send and assert:

```ts
expect(await f.ports.outbox.flush()).toEqual({ sent: 0, invalidated: 1 });
expect(f.ports.outbox.accepted).toHaveLength(0);
expect((await loadBackgroundDraft(draftId, unauthorizedActor, f.ports)).kind).toBe('denied');
```

Also assert the card shows delivery estimate `0.02 USD` separately from actual investigation `0.07 USD`. Re-estimation to `0.03 USD` at approval or send must produce a new review version with no send until reapproved; unavailable estimation defers. A timestamp-only refresh with unchanged amount/unit/input digest retains approval. After unresolved model usage settles, reload the card and assert that actual/held amounts update while the delivery estimate and draft version remain unchanged.

Repeat for unknown authorization, audience membership changes, task becoming complete, changed source revision, and an approval posted for a superseded draft version. Each must block delivery without rewriting approved text. For deletion before approval, deletion after approval while queued, and refresh-detected absence without an event, assert `withdrawn`, no usable approval token and zero provider sends. Include deletion of unquoted source context, and a barrier that delivers deletion between presence refresh and the approval/dispatch transaction. The final local generation check must reject that race. Test rejected drafts, forged audience/evidence IDs, current quiet-hours deferral, and sanitized inspection for a non-authorized operator.

- [ ] **Step 2: Run `npm test -- tests/background/delivery.test.ts`.** Expect the missing background evidence/approval guards to fail.
- [ ] **Step 3: Implement review and outbox adapters.** Enforce full-context review access; refresh source presence, authorization, disclosure and material work state, and obtain the adapter estimate at approval and final send; persist approval/delivery intent atomically after checking the dependency generations and draft state. Bind the estimate to approval; change creates a new version requiring approval, unavailability defers, and deletion withdraws/cancels. Keep the local dispatch fence adjacent to the actual outbox send and document the cross-provider race limit from the design. Use the existing outbox's idempotent enqueue and uncertain-send reconciliation, extending its metadata/eligibility contract rather than adding a sender. Invalidation requires reevaluation and fresh approval. Uncertain sends must still reconcile after revocation or deletion, without issuing a new send for a withdrawn draft.
- [ ] **Step 4: Rerun delivery tests and the existing outbox tests via `npm test`.** Expect pass and no regression in chat-derived delivery or existing approval/quiet-hours behavior.
- [ ] **Step 5: Commit locally.** Suggested message: `feat: review and deliver authorized background drafts`.

## Task 6: First useful shared-inbox slice and operational handoff

**Files:** Create `register.ts`, `tests/background/inbox.test.ts`, `docs/background-suggestions.md`; modify the actual service composition root only to register the new handler/adapters.

**Interfaces:** `registerBackground(ports: BackgroundPorts, config: BackgroundConfig): BackgroundRegistration`, where `BackgroundConfig` has `enabled: boolean`, `inboxAllowlist: string[]`, and `dailyBudgetUnits: bigint`; defaults are false, empty and zero. `BackgroundRegistration.ingest(envelope: EvidenceEnvelope): Promise<IngestResult>` and `BackgroundRegistration.observeDeletion(observation: DeletionObservation): Promise<DeletionResult>` are the existing adapter callback targets. The deletion callback commits immediately without waiting for a due evaluation. Register the job kind `external_evidence`; use a 120-second lease and the existing ten-second scheduler.

- [ ] **Step 1: Write `inbox_to_costed_review_to_reconciled_delivery`.** Intake a useful restricted shared-inbox update, advance the fake clock 30 seconds, execute due work, and assert one draft with why-now, evidence, its eligible restricted audience, a delivery estimate and separate actual investigation spend. A broad project-channel audience must be excluded. There must be no send until that individual version and displayed estimate are approved. Crash after fake provider acceptance but before outbox acknowledgement; deliver a source deletion observation while the result is uncertain; restart the worker on the persisted DB and assert that reconciliation confirms the single historical send without issuing another:

```ts
await f.restart();
await f.ports.scheduler.runDue();
await f.ports.outbox.flush();
expect(f.ports.outbox.accepted).toHaveLength(1);
expect(await f.state()).toMatchObject({ outboxState: 'delivered', activeDrafts: 0 });
```

Add cases for crash after intake commit, after model admission, after decision commit, and after idempotent enqueue. Also demonstrate already-handled quiet, denied/unknown access, a useful later inbox revision and disable/allowlist behavior. Add deletion before publication, before approval, after approval before dispatch, and absence detected on refresh with its event delayed; assert withdrawn state and zero sends. Demonstrate unavailable/changed estimates and incomplete investigation settlement without collapsing them into one cost figure. Assert each has a persisted understandable outcome and no unapproved send.

- [ ] **Step 2: Run `npm test -- tests/background/inbox.test.ts`.** Expect absent wiring/restart behavior to fail.
- [ ] **Step 3: Implement registration and document the operator contract.** Wire existing adapter, scheduler, gateway, policy, panel and outbox ports. Expose sanitized quiet/deferred/failed/withdrawn counts, estimate failure/change counts, next due time, transient failures, reservations, and authorized requeue through the existing inspection surface. Document the exact limits, restricted evidence display, separate cost fields, deletion withdrawal/restoration, estimate-bound approval invalidation, uncertain-send behavior and its external-race limitation, kill switch and local fixture demonstration. Include configuration disabled by default and the distinction between deterministic validation and model usefulness.
- [ ] **Step 4: Run `npm test` and the persisted-database restart scenario.** Expect all existing and new checks to pass, exactly one accepted send in the crash scenario, zero unapproved sends, and zero sends in every locally known pre-dispatch deletion case. Record outcomes and observed fake workload timing; do not claim a production load target or real-model usefulness. This is the first useful local delivery when the entire inbox flow passes, not when Task 1 alone passes.
- [ ] **Step 5: Commit locally.** Suggested message: `feat: complete shared-inbox background suggestion flow`.

## Task 7: Add repository activity and feedback through the same evaluator

This follows the inbox slice; it is not a prerequisite for demonstrating that slice. Its independently reviewable deliverable is source coverage using unchanged reasoning and safety contracts.

**Files:** Extend `contracts.ts` normalization, `register.ts`, `tests/background/sources.test.ts`, `docs/background-suggestions.md` and source adapter registration at discovered existing paths.

**Interfaces:** `normalizeExternalEvidence(kind: EvidenceEnvelope['sourceKind'], connectionId: string, payload: AdapterEvidence): EvidenceEnvelope`. `AdapterEvidence` is the existing authenticated adapter payload type plus a feedback submission-ID projection; use existing fields, not a second source ingestion protocol. All outputs call the same `ingestEvidence` and `external_evidence` handler. Extend `BackgroundConfig` with `repositoryAllowlist: string[]` and `feedbackAllowlist: string[]`, both defaulting to empty; per-source enablement remains off until explicitly configured.

- [ ] **Step 1: Write repository/feedback identity, disclosure, deletion and correlation tests.** Duplicate feedback submission `s1` across different delivery IDs gives one evidence item/evaluation; `s2` remains distinct without inventing revision history. Repository revision `r2` after `r1` can be reevaluated. An inbox and repository resource authoritatively linked to task `t7` produce one active suggestion; an unlinked feedback submission remains separate. Deletion/absence from repository and feedback adapters must use the same withdrawal path, including stable feedback submission identity without revision history. Assert restricted inbox influence still cannot reach the broad project channel:

```ts
expect(inboxOutcome.snapshot.audiences.map(a => a.id)).not.toContain('project-channel');
expect(inboxOutcome.snapshot.dependencies.some(d => d.scopeRef === 'inbox-team')).toBe(true);
expect(await f.state()).toMatchObject({ evaluatorKinds: ['external_evidence'] });
```

- [ ] **Step 2: Run `npm test -- tests/background/sources.test.ts`.** Expect missing source registrations/normalization to fail.
- [ ] **Step 3: Implement source normalization and registration only.** Supply stable feedback submission identity, source-specific content/presence reads, deletion callbacks, scopes and independent enablement. Keep context assembly, model loop, cost separation, withdrawal, policy and outbox shared. Document the authoritative-link limit on cross-source duplicate detection.
- [ ] **Step 4: Run `npm test`.** Expect repository, inbox, feedback and existing chat flows to pass with the same evaluator and no weakening of restricted-source tests.
- [ ] **Step 5: Commit locally.** Suggested message: `feat: extend background suggestions to repository activity and feedback`.

## Qualification and execution boundary

The plan's acceptance fixtures prove durable mechanics and authorization enforcement under deterministic adapters. They do not prove that a real model notices the right work or stays quiet appropriately. No source setup, model run, installation, implementation or production change is part of this planning pass.

Before later production enablement, separately authorize a draft-only real-model assessment of selected shared-inbox examples. Have reviewers assess both suggestions and quiet decisions for usefulness, redundancy, faithful evidence and audience correctness; record investigation actuals and unresolved reservations separately from delivery estimates, plus latency. Verify source-deletion withdrawal before approval and dispatch, including late-event and refresh-only cases. Select an actual production load and budget target from measured source volume before load qualification. Require zero unauthorized disclosures, unapproved sends and sends after a locally observed pre-dispatch deletion in the qualification set, and agree usefulness/cost acceptance thresholds before interpreting the results. Keep delivery manual through the existing approval path in any pilot.

There is no blocker to producing this plan from the supplied packet and later update. The supplied APIs do not establish atomicity between a remote deletion and provider acceptance; the precise remaining race and the stronger guarantee requiring additional provider support are explicit in the design. Exact existing integration filenames/API shapes, actual model quality, actual throughput and an owner-approved production allocation remain unverified execution/rollout inputs. The proposed design resolves the runtime, state, context, authorization, recovery and delivery choices now. [Process receipt and checks](receipt.md) record how these artifacts were produced.
