# Nightly recommendation service: handoff readiness review

The complete design is not ready for implementation. It describes desired properties but leaves the mechanisms that determine the system's behavior to stage 2. The known, suitable intake contract supports bounded intake work now; that does not make the requested complete system design ready.

This review preserves the draft and lists gaps separately. It does not choose the missing design. The only evidence is Case 4 in `../../../eval-fixtures/concrete-handoffs.md`.

## Supplied draft — unchanged

Reuse the existing event inbox. A worker will collect relevant context and run a bounded model to choose whether to recommend an action. It will select the appropriate audience, preserve permissions and avoid redundant recommendations. Persist results and retry failures safely. Stage 1 adds durable intake; stage 2 adds reasoning; stage 3 connects delivery. Acceptance is that representative inputs produce useful, authorized recommendations. Choose the model runtime and context/authorization mechanism when implementing stage 2. The intake stage can start now.

## Material gaps to resolve in the complete design

| Gap | Why it blocks the handoff | Smallest useful correction or observation |
|---|---|---|
| Runtime and enforcement of bounds are explicitly deferred. | The implementer must choose the execution model, tools, admission and cancellation behavior before knowing what a run can safely do or cost. | Select the runtime, identify the host/model boundary, and define the enforced call/tool/cost/time limits and behavior on refusal or exhaustion. Establish any prerequisite capability from its owning source. |
| Context collection and work association have no rules. | “Relevant context” leaves retrieval scope, authoritative records, stale/conflicting facts and the unit of work undefined. Different implementations could recommend different actions for the same inputs. | Specify context inputs and read interfaces, how evidence is assigned to work, which sources win conflicts, and when missing information requires silence or deferral. |
| Audience and permission preservation have no mechanism. | There is no identity/principal, disclosure rule, audience-selection rule or access-recheck point. “Authorized recommendations” therefore cannot be assessed, including after access changes. | Define the authorization and audience contract from retrieval through persisted results and delivery, with deny/unknown and revocation behavior. Verify the required checks exist before treating them as integration work. |
| Identity, novelty and state are undefined. | The draft cannot distinguish a delivery retry from a useful later update, or tell whether work is already being handled. Persistence alone does not prevent duplicates. | Define event/work/decision identities, the state that records considered evidence and prior recommendations, and the rule for suppressing versus revisiting work. Include a retry and a later-update example. |
| Recovery and delivery boundaries are unspecified. | A crash between reasoning, persistence and sending can lose work or duplicate it. There is no behavior for partial results, expired workers or uncertain sends. The draft also does not establish who, if anyone, authorizes delivery. | State transaction and retry boundaries, ownership of attempts, terminal/deferred states, delivery authority and uncertain-send reconciliation. Walk through a crash before and after each consequential boundary. |
| Nightly scheduling and stage completion are not designed. | The design does not define the nightly window, items included in a run, late arrivals, overlapping nights, backlog or what each stage makes possible. “Intake, reasoning, delivery” is sequencing, not evidence of completion. | Define the run-selection and catch-up policy, then give each stage a dependency and observable result consistent with the chosen architecture. |
| Acceptance cannot distinguish correctness from usefulness. | “Representative” and “useful” have no case set, judging method or failure criteria. It is possible to pass a happy-path demo while authorization, novelty or recovery fails. | Specify representative normal, ambiguous and failure cases; separate deterministic authorization/recovery assertions from a documented usefulness assessment. Do not invent numerical quality thresholds without a basis. |

These are design blockers for the complete system, not requests for more prose or a new user interview. Technical choices can be made within the delegated scope, but they must be made and explained before the design is declared ready.

## Work that can begin and the next handoff

Intake work can proceed within its known contract if it does not silently commit the downstream work identities, authorization model or delivery semantics. The packet establishes that the existing intake is suitable; this review has not inspected or tested it. The draft should explain what “adds durable intake” means when reusing that foundation and give that bounded stage an exit condition.

The next useful action is to complete the missing design contracts, then trace one normal recommendation, one ambiguity or access failure, one duplicate retry and one later update through the complete flow. Recheck that each stage delivers its promised behavior and that acceptance can demonstrate it. Polishing wording or approving intake as a prototype would not satisfy the request for a complete design.

Checks performed here: compared the draft against the requested scope and the planning skill's handoff questions. No runtime, access mechanism, persistence behavior, live workflow or usefulness outcome was verified. No edits to the supplied draft were made.
