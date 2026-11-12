# Background Work Suggestions Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a reusable background evaluator that turns new external evidence and current work context into an authorized review draft or an explicit quiet/deferred outcome, beginning with a complete repository slice.

**Architecture:** Add an external-evidence job handler to the existing TypeScript/SQLite service and run a bounded, host-mediated tool loop through the structured-model gateway. Reuse the scheduler, leased workers, maintained domain instructions, connection-scoped reads, review panel and reconciling outbox. Inbox and feedback later enter the same evaluator through normalization adapters.

**Tech Stack:** TypeScript, SQLite, existing structured-model gateway, existing deterministic adapter fakes, `npm test`; no new runtime or infrastructure dependency.

**Spec:** [Proposed system design](case-1-design.md). Read it with this plan.

**Status:** Proposed engineering choices, not approved implementation. The execution-subskill notice above is preserved from the authoring method; this planning pass invokes neither execution skill, performs no implementation and requests no execution-method choice. Technical choices were delegated; design approval was not implied.

## Global Constraints

- Drafts appear in a review panel. A person approves an individual draft before existing delivery machinery sends it. No automatic tasks or external messages.
- Preserve each source's disclosure restrictions through retrieval, drafts and delivery.
- Exact source/delivery retries must not produce duplicate work or drafts; a later update about the same work may be useful.
- Avoid redundant suggestions about work already being handled.
- Start with repository activity; inbox and feedback must use the same reasoning service.
- Keep costs bounded and failed/deferred work inspectable. Current quiet-hours and approval policies remain in force.
- Implementation language and storage remain TypeScript and SQLite; use the existing scheduler, gateway, read APIs, review panel and outbox.

## Review Focus

These implied failure modes are explicitly added to the owning task's tests below:

1. An old repository revision delivered after a newer one must not restore stale work state — Task 2.
2. Permission revoked for unquoted context must prevent review/delivery just as revoked cited evidence does — Task 5.
3. A stale conversation summary or learned owner association must not override current mapping/directory/task records — Task 2.
4. Two resources linked to the same task, or an update during a leased evaluation, must not publish competing/stale drafts — Task 4.
5. A process crash after provider acceptance but before acknowledgement must reconcile to one send — Task 6.

---

## File map and integration boundaries

All paths below are proposed additions, not claims about an inspected repository. Locate the actual composition root, migration registration, review handlers and outbox eligibility extension at implementation time; their existing filenames and line numbers were not supplied. Integrate the named contracts below at those four seams and retain existing conventions. No repository reorganization is planned.

| Proposed file | Responsibility |
|---|---|
| `src/background/contracts.ts` | Normalized evidence, dependencies, decision and job types shared by tasks |
| `src/background/001-background.sql` | Receipt/evidence/cursor/evaluation, suggestion-claim and reservation schema; reuse jobs/drafts/outbox |
| `src/background/store.ts` | Atomic intake, generation fencing, evaluation publication and inspection queries |
| `src/background/context.ts` | Current context, authority rules, work/audience resolution and restricted read facade |
| `src/background/evaluate.ts` | Maintained instructions, typed decision validation and bounded model/tool loop |
| `src/background/budget.ts` | Durable background quota/call reservations layered around gateway admission |
| `src/background/review.ts` | Authorized review, immutable version approval/rejection and delivery intent |
| `src/background/delivery.ts` | Existing outbox evidence adapter, final eligibility checks and idempotent enqueue |
| `src/background/register.ts` | Repository intake/job registration and mapping existing service adapters into ports |
| `tests/background/fixture.ts` | Temporary SQLite and deterministic fake adapters; restart against the same DB |
| `tests/background/{intake,context,evaluate,lifecycle,delivery,repository,sources}.test.ts` | Focused contract and integration checks |
| `docs/background-suggestions.md` | Operator states, limits, review behavior, verification and enablement criteria |

The production `BackgroundPorts` type is an adapter boundary to the existing scheduler, gateway, source reads, project/directory/task/conversation reads, policy and outbox; it does not introduce implementations of those services. Every tool read returns a `ReadDependency` containing connection, resource, revision where available and disclosure-scope reference. Existing SDK/model types should be imported rather than redefined.

The test fixture exports `createFixture(): Promise<BackgroundFixture>` and `repository(overrides?: Partial<EvidenceEnvelope>): EvidenceEnvelope`. Its default repository envelope is connection `c1`, source `repo`, resource `pr-7`, revision `r1`, delivery `d1`, content reference `ref:pr-7:r1`, at a fixed fake clock. `BackgroundFixture` exposes `db`, `ports`, `lease`, `input`, `clock`, `state()` and `restart()`. `state()` queries counts, decisions, draft versions, job statuses/due times and reservation totals from persisted state. Fake controls used below are added alongside their owning task: `source.current`, `source.access`, `directory.roles`, `tasks.records`, `gateway.decisions`, `gateway.calls`, `outbox.accepted`, `outbox.uncertain`, and named fault barriers. They wrap supplied deterministic fakes; these are proposed test APIs, not asserted existing APIs.

## Task 1: Durable intake and evidence identity

**Files:** Create `contracts.ts`, `001-background.sql`, `store.ts`, `tests/background/fixture.ts` and `tests/background/intake.test.ts` at the paths above. Register the SQL with the existing migration mechanism.

**Interfaces:**

- `EvidenceEnvelope = { connectionId: string; sourceKind: 'repository' | 'inbox' | 'feedback'; sourceId: string; deliveryId: string; resourceId: string; revision: string | null; submissionId?: string; occurredAt: string; contentRef: string }`. The host supplies `connectionId`; feedback must include its stable `submissionId`.
- `ingestEvidence(db: BackgroundDb, envelope: EvidenceEnvelope, now: Date): Promise<IngestResult>`, where `IngestResult.kind` is `new_evidence | duplicate_delivery | duplicate_revision | intake_conflict` and includes `evidenceId` when applicable. `BackgroundDb` wraps the existing SQLite connection/transaction API.
- `EvaluationInput = { resourceKey: string; generation: number; evidenceIds: string[] }`; `JobLease = { jobId: string; fence: string; expiresAt: Date }`. The scheduler constructs these from existing persisted job data.

- [ ] **Step 1: Write `deduplicates_delivery_but_accepts_new_revision` and transaction-failure tests.** Assert the following sequence, then separately inject a failure before transaction commit and assert zero receipt/evidence/job writes. Also test a new delivery of `r1` and a conflicting reuse of `d1`.

```ts
const f = await createFixture();
expect((await ingestEvidence(f.db, repository(), f.clock.now())).kind).toBe('new_evidence');
expect((await ingestEvidence(f.db, repository(), f.clock.now())).kind).toBe('duplicate_delivery');
expect((await ingestEvidence(f.db, repository({ deliveryId: 'd2', revision: 'r2' }), f.clock.now())).kind).toBe('new_evidence');
expect(await f.state()).toMatchObject({ receipts: 2, evidence: 2, resourceJobs: 1, generation: 2 });
```

- [ ] **Step 2: Run `npm test -- tests/background/intake.test.ts`.** Expect failure from missing background intake/schema or unmet assertions. If the repository test runner does not accept file arguments, use `npm test` and confirm these named tests fail.
- [ ] **Step 3: Implement `ingestEvidence` and its schema.** Use the spec's distinct delivery/evidence uniqueness keys, immutable receipt linkage, atomic generation increment and one resource job. Set the first due time to intake + 30 seconds; later intake must not indefinitely extend it. Create the evaluation, active-work claim and cost-ledger tables needed by later tasks in the same migration. Make the logical evaluation ID unique to `(resourceKey, generation)` and reuse it across attempts; pending unclassified intake is host-only. Reject invalid identity fields without storing source content in logs.
- [ ] **Step 4: Run the intake tests.** Expect all to pass, including the conflicting-payload and rollback cases; inspect that retrying rolled-back intake creates exactly one evidence row and one job.
- [ ] **Step 5: Commit the completed intake/schema/test change locally.** Suggested message: `feat: persist external evidence and coalesced background jobs`.

## Task 2: Authorized context and authoritative work routing

**Files:** Create `context.ts`, `tests/background/context.test.ts`; extend `contracts.ts` and the test fixture.

**Interfaces:**

- `ReadDependency = { connectionId: string; resourceId: string; revision: string | null; scopeRef: string }`.
- `ContextSnapshot = { workKey: string; audiences: AudienceHandle[]; evidenceIds: string[]; newEvidenceIds: string[]; dependencies: ReadDependency[]; resourceRevisions: Record<string, string | null>; digest: string; modelContext: string }`. `AudienceHandle = { id: string }` is host-issued; directory/policy metadata stays host-side.
- `assembleContext(input: EvaluationInput, ports: BackgroundPorts, signal: AbortSignal): Promise<ContextResult>`, where `ContextResult` is `{kind:'ready'; snapshot:ContextSnapshot}` or `{kind:'defer'|'denied'; reason:string}`.
- `readBackgroundTool(request: BackgroundReadRequest, session: ContextSession): Promise<AuthorizedReadResult>` shares the same authorization, dependency ledger, eight-read/32-KiB bounds and principal. `ContextSession` owns the input, ports, counters and collected dependencies. `BackgroundReadRequest` is a discriminated union of source/project/conversation/task reads with host-issued handles; `AuthorizedReadResult` contains authorized bounded content or a sanitized denial/defer reason. No raw connection override is accepted.

- [ ] **Step 1: Write `uses_current_revision_and_authority`, `fails_closed_on_unknown`, and `tracks_unquoted_context`.** Fixture: deliver `r2`, then late `r1`; source says current `r2`; summary suggests Alice, current directory says Bob; task `t7` links `pr-7`. Assert:

```ts
const result = await assembleContext(f.input, f.ports, new AbortController().signal);
expect(result.kind).toBe('ready');
if (result.kind !== 'ready') throw new Error(result.reason);
expect(result.snapshot.workKey).toBe('task:t7');
expect(result.snapshot.resourceRevisions['pr-7']).toBe('r2');
expect(result.snapshot.audiences).toEqual([{ id: 'reviewers-for-bob' }]);
expect(result.snapshot.dependencies.map(d => d.resourceId)).toContain('conversation-9');
```

The fixture's host-issued audience `reviewers-for-bob` must come from current policy/roles. Also assert unknown access returns `defer` without a source-content read; ambiguous task/project mapping defers; a restricted conversation cannot authorize the project-channel audience; a tool request that changes the principal is rejected. No-current-revision evidence must defer stale-sensitive work.

- [ ] **Step 2: Run `npm test -- tests/background/context.test.ts`.** Expect the named assertions to fail before implementation.
- [ ] **Step 3: Implement the two context functions.** Read current source state, stable mapping/current directory, current linked tasks, then permitted hints/history. Use exact task resource links for canonical work identity. Maintain all consumed scopes and validate audience intersection; do not let citations reduce that ledger. Assemble initial reads and later tool reads through one counter/authorization path. Tool content is explicitly labeled untrusted evidence.
- [ ] **Step 4: Rerun the context tests.** Expect pass, with no denied-content call and no fallback routing from stale/conflicting hints.
- [ ] **Step 5: Commit locally.** Suggested message: `feat: assemble authorized background work context`.

## Task 3: Cost-admitted bounded decisions

**Files:** Create `evaluate.ts`, `budget.ts`, `tests/background/evaluate.test.ts`; extend contracts and fake gateway controls.

**Interfaces:**

- `BackgroundDecision` is the spec's `quiet`, `defer` or `draft` union. A draft has `workKey`, `audienceId`, `nextStepKind`, `body`, `supportingEvidenceIds`, `newEvidenceIds`, `whyNow`. `nextStepKind` is exactly `request_review | request_status | report_blocker | suggest_follow_up`.
- `evaluateBackground(input: EvaluationInput, lease: JobLease, ports: BackgroundPorts, signal: AbortSignal): Promise<EvaluationOutcome>`. `EvaluationOutcome` includes a decision or operational reason, snapshot when obtained, persisted call/reservation IDs and usage; it does not publish a draft or send anything.
- `reserveBackgroundCall(db: BackgroundDb, evaluationId: string, ceilingUnits: bigint, now: Date): Promise<ReservationResult>`; `settleBackgroundCall(db: BackgroundDb, reservationId: string, actualUnits: bigint | null): Promise<void>`. `ReservationResult` is admitted with ID/ordinal or refused with reason. Null usage retains the ceiling. Gateway admission still runs after local reservation.

- [ ] **Step 1: Write tests for admission refusal, limits, hostile evidence and crash-safe accounting.** For `refusal_calls_no_model`, seed exhausted background allocation and assert zero gateway calls plus deferred reason `budget`. For `settles_once`, reserve 10 units in a 20-unit test allocation, settle 4 twice, and assert 4 charged and 16 available. For `retains_unknown_cost_across_restart`, leave usage unknown, restart, and assert all 10 units remain held.

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

## Task 4: Fenced publication, novelty and recovery

**Files:** Extend `store.ts`; create `tests/background/lifecycle.test.ts`; extend persisted-state/fault-barrier fixture support.

**Interfaces:**

- `publishEvaluation(db: BackgroundDb, input: EvaluationInput, lease: JobLease, outcome: EvaluationOutcome, now: Date): Promise<PublishResult>` where `PublishResult.kind` is `draft | quiet | deferred | stale | lease_lost` and carries a draft ID/version when applicable.
- `scheduleBackgroundOutcome(db: BackgroundDb, lease: JobLease, reason: string, now: Date): Promise<void>` applies retry/defer/park policy using existing job attempts/next-due fields and explicit transient-failure metadata.
- A persisted `ReviewDraft` contains `id`, integer `version`, `workKey`, `audienceId`, immutable body, evidence IDs, dependency ledger, context digest and review state. Existing panel storage gains these fields/reference links; it is not replaced.

- [ ] **Step 1: Write `new_generation_invalidates_inflight_publication`, `one_pending_draft_per_work`, and novelty/recovery tests.** Pause the first evaluation before publication; ingest `r2`; resume and assert:

```ts
expect((await publishEvaluation(f.db, oldInput, oldLease, oldOutcome, f.clock.now())).kind).toBe('stale');
expect(await f.state()).toMatchObject({ drafts: 0, generation: 2, resourceJobs: 1 });
```

Race two resources linked to `task:t7` and assert one active draft, including when candidate audiences differ. Assert the hidden competing claim's details never enter model context. Same-evidence retries and a rejected version yield no new draft; a new material revision may produce a new version. An already-active matching task action is quiet; a distinct new blocker can be drafted. New events during an approved pending delivery wait for reconciliation. Lost lease publication must write no draft.

Add fake-clock assertions for transient retry delays of 1 minute, 5 minutes, 30 minutes and 2 hours, failure on the fifth error, budget/unknown-access deferral of 15 minutes without increasing transient failures, and parked state after 24 hours of unresolved deferral. Existing quiet-hours eligibility overrides the due time as specified; test its later next-eligible time directly.

- [ ] **Step 2: Run `npm test -- tests/background/lifecycle.test.ts`.** Expect missing publication/claim/recovery behavior to fail.
- [ ] **Step 3: Implement the publication transaction and scheduling policy.** Check generation and lease fence; record every decision; claim canonical work atomically; compare active tasks and draft/delivery history; create or replace only unapproved draft versions. Preserve sent/rejected history for material-new-evidence comparison. Persist quiet as successful completion and failed/deferred reasons for authorized inspection. Requeue refreshes context and never deletes existing outbox idempotency state.
- [ ] **Step 4: Rerun lifecycle tests.** Expect pass, including both orders of the parallel publication race and all fake-clock states.
- [ ] **Step 5: Commit locally.** Suggested message: `feat: publish fenced background drafts and inspectable outcomes`.

## Task 5: Individual review and existing outbox delivery

**Files:** Create `review.ts`, `delivery.ts`, `tests/background/delivery.test.ts`; extend the existing review handlers and outbox evidence/eligibility seam at their discovered paths.

**Interfaces:**

- `loadBackgroundDraft(draftId: string, actorId: string, ports: BackgroundPorts): Promise<ReviewAccessResult>` returns an authorized review card or sanitized denied result.
- `approveBackgroundDraft(draftId: string, version: number, actorId: string, ports: BackgroundPorts): Promise<ApprovalResult>` returns `approved | stale | denied | deferred` and persists an immutable approval plus durable delivery job atomically.
- `rejectBackgroundDraft(draftId: string, version: number, actorId: string, ports: BackgroundPorts): Promise<void>` records a version-specific rejection after authorization.
- `enqueueBackgroundDelivery(draftId: string, version: number, ports: BackgroundPorts): Promise<DeliveryResult>` returns `queued | already_queued | invalidated | deferred`; the outbox uses key `background:<draftId>:<version>`. The existing send-boundary eligibility hook rechecks every dependency and current work state.

- [ ] **Step 1: Write `requires_current_individual_approval` and revocation/change tests.** Seed a draft consuming repository evidence plus an unquoted restricted conversation. Before approval assert zero outbox entries. Approve as an authorized reviewer and assert one entry with its exact version; repeat and assert no second entry. Then revoke the conversation before send and assert:

```ts
expect(await f.ports.outbox.flush()).toEqual({ sent: 0, invalidated: 1 });
expect(f.ports.outbox.accepted).toHaveLength(0);
expect((await loadBackgroundDraft(draftId, unauthorizedActor, f.ports)).kind).toBe('denied');
```

Repeat for unknown authorization, audience membership changes, task becoming complete, changed source revision, and an approval posted for a superseded draft version. Each must block delivery without rewriting approved text. Test rejected drafts, forged audience/evidence IDs, current quiet-hours deferral, and sanitized inspection for a non-authorized operator.

- [ ] **Step 2: Run `npm test -- tests/background/delivery.test.ts`.** Expect the missing background evidence/approval guards to fail.
- [ ] **Step 3: Implement review and outbox adapters.** Enforce full-context review access; refresh authorization, disclosure and material work state at approval and final send; persist approval/delivery intent atomically. Use the existing outbox's idempotent enqueue and uncertain-send reconciliation, extending its metadata/eligibility contract rather than adding a sender. Invalidation requires reevaluation and fresh approval. Uncertain sends must still reconcile after revocation, without issuing a new send.
- [ ] **Step 4: Rerun delivery tests and the existing outbox tests via `npm test`.** Expect pass and no regression in chat-derived delivery or existing approval/quiet-hours behavior.
- [ ] **Step 5: Commit locally.** Suggested message: `feat: review and deliver authorized background drafts`.

## Task 6: First useful repository slice and operational handoff

**Files:** Create `register.ts`, `tests/background/repository.test.ts`, `docs/background-suggestions.md`; modify the actual service composition root only to register the new handler/adapters.

**Interfaces:** `registerBackground(ports: BackgroundPorts, config: BackgroundConfig): BackgroundRegistration`, where `BackgroundConfig` has `enabled: boolean`, `repositoryAllowlist: string[]`, and `dailyBudgetUnits: bigint`; defaults are false, empty and zero. `BackgroundRegistration.ingest(envelope: EvidenceEnvelope): Promise<IngestResult>` is the existing adapter callback target. Register the job kind `external_evidence`; use a 120-second lease and the existing ten-second scheduler.

- [ ] **Step 1: Write `repository_to_review_to_reconciled_delivery`.** Intake a useful repository update, advance the fake clock 30 seconds, execute due work, and assert one draft with why-now, evidence and audience. There must be no send until that individual version is approved. Crash after fake provider acceptance but before outbox acknowledgement, restart the worker on the persisted DB, and assert:

```ts
await f.restart();
await f.ports.scheduler.runDue();
await f.ports.outbox.flush();
expect(f.ports.outbox.accepted).toHaveLength(1);
expect(await f.state()).toMatchObject({ outboxState: 'delivered', activeDrafts: 0 });
```

Add cases for crash after intake commit, after model admission, after decision commit, and after idempotent enqueue. Also demonstrate already-handled quiet, denied/unknown access, a useful later revision and disable/allowlist behavior. Assert each has a persisted understandable outcome and no unapproved send.

- [ ] **Step 2: Run `npm test -- tests/background/repository.test.ts`.** Expect absent wiring/restart behavior to fail.
- [ ] **Step 3: Implement registration and document the operator contract.** Wire existing adapter, scheduler, gateway, policy, panel and outbox ports. Expose sanitized quiet/deferred/failed counts, next due time, transient failures, reservations, and authorized requeue through the existing inspection surface. Document the exact limits, restricted evidence display, approval invalidation, uncertain-send behavior, kill switch and local fixture demonstration. Include configuration disabled by default and the distinction between deterministic validation and model usefulness.
- [ ] **Step 4: Run `npm test` and the persisted-database restart scenario.** Expect all existing and new checks to pass, exactly one accepted send in the crash scenario, and zero unapproved sends. Record outcomes and observed fake workload timing; do not claim a production load target or real-model usefulness. This is the first useful local delivery when the entire repository flow passes, not when Task 1 alone passes.
- [ ] **Step 5: Commit locally.** Suggested message: `feat: complete repository background suggestion flow`.

## Task 7: Add inbox and feedback through the same evaluator

This follows the repository slice; it is not a prerequisite for demonstrating that slice. Its independently reviewable deliverable is source coverage using unchanged reasoning and safety contracts.

**Files:** Extend `contracts.ts` normalization, `register.ts`, `tests/background/sources.test.ts`, `docs/background-suggestions.md` and source adapter registration at discovered existing paths.

**Interfaces:** `normalizeExternalEvidence(kind: EvidenceEnvelope['sourceKind'], connectionId: string, payload: AdapterEvidence): EvidenceEnvelope`. `AdapterEvidence` is the existing authenticated adapter payload type plus a feedback submission-ID projection; use existing fields, not a second source ingestion protocol. All outputs call the same `ingestEvidence` and `external_evidence` handler. Extend `BackgroundConfig` with `inboxAllowlist: string[]` and `feedbackAllowlist: string[]`, both defaulting to empty; per-source enablement remains off until explicitly configured.

- [ ] **Step 1: Write inbox/feedback identity, disclosure and correlation tests.** Duplicate feedback submission `s1` across different delivery IDs gives one evidence item/evaluation; `s2` remains distinct without inventing revision history. Inbox revision `m2` after `m1` can be reevaluated. An inbox and repository resource authoritatively linked to task `t7` produce one active suggestion; an unlinked feedback submission remains separate. Assert restricted inbox influence cannot reach the broad project channel:

```ts
expect(inboxOutcome.snapshot.audiences.map(a => a.id)).not.toContain('project-channel');
expect(inboxOutcome.snapshot.dependencies.some(d => d.scopeRef === 'inbox-team')).toBe(true);
expect(await f.state()).toMatchObject({ evaluatorKinds: ['external_evidence'] });
```

- [ ] **Step 2: Run `npm test -- tests/background/sources.test.ts`.** Expect missing source registrations/normalization to fail.
- [ ] **Step 3: Implement source normalization and registration only.** Supply stable feedback submission identity, source-specific content reads/scopes and independent enablement. Keep context assembly, model loop, policy and outbox shared. Document the authoritative-link limit on cross-source duplicate detection.
- [ ] **Step 4: Run `npm test`.** Expect repository, inbox, feedback and existing chat flows to pass with the same evaluator and no weakening of restricted-source tests.
- [ ] **Step 5: Commit locally.** Suggested message: `feat: extend background suggestions to inbox and feedback`.

## Qualification and execution boundary

The plan's acceptance fixtures prove durable mechanics and authorization enforcement under deterministic adapters. They do not prove that a real model notices the right work or stays quiet appropriately. No source setup, model run, installation, implementation or production change is part of this planning pass.

Before later production enablement, separately authorize a draft-only real-model assessment of selected repository examples. Have reviewers assess both suggestions and quiet decisions for usefulness, redundancy, faithful evidence and audience correctness; record cost and latency. Select an actual production load and budget target from measured source volume before load qualification. Require zero unauthorized disclosures/unapproved sends in the qualification set, and agree usefulness/cost acceptance thresholds before interpreting the results. Keep delivery manual through the existing approval path in any pilot.

There is no planning blocker in the supplied packet. Exact existing integration filenames/API shapes, actual model quality, actual throughput and an owner-approved production allocation remain unverified execution/rollout inputs. The proposed design resolves the runtime, state, context, authorization, recovery and delivery choices now. [Process receipt and checks](receipt.md) record how these artifacts were produced.
