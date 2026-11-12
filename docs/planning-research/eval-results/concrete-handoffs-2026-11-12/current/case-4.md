# Readiness review

**Not ready for implementation as the complete system design requested.** The draft states the desired behavior and a delivery sequence, but leaves the central runtime, context, authorization and recovery contracts undefined. Suitable intake is established by the supplied facts; it does not settle those later dependencies. The preserved draft follows, with material gaps listed separately.

## Preserved draft

> Reuse the existing event inbox. A worker will collect relevant context and run a bounded model to choose whether to recommend an action. It will select the appropriate audience, preserve permissions and avoid redundant recommendations. Persist results and retry failures safely. Stage 1 adds durable intake; stage 2 adds reasoning; stage 3 connects delivery. Acceptance is that representative inputs produce useful, authorized recommendations. Choose the model runtime and context/authorization mechanism when implementing stage 2. The intake stage can start now.

## Material gaps

| Gap | Why it blocks readiness | What the design must resolve |
|---|---|---|
| **G1 — Runtime and execution boundary** | “Bounded model” does not identify who runs it, which capabilities it has, who enforces limits, or how those limits interact with retries. Deferring runtime selection to stage 2 leaves a consequential architecture choice outside the complete design. | Select the runtime and its host responsibilities, including allowed tools, admission, execution/cost limits, cancellation and exhaustion behavior. No particular runtime can be recommended from the supplied evidence. |
| **G2 — Context, work identity and audience authority** | “Relevant context,” “appropriate audience” and avoiding redundancy are promised outcomes without a mechanism. The implementer cannot know which sources establish ongoing work or resolve conflicting associations and recipients. | Define available context, authoritative versus advisory records, the basis for associating events with work, and the rules for choosing or withholding an audience. |
| **G3 — Access and disclosure lifecycle** | “Preserve permissions” does not establish whose access governs retrieval, what reaches the model, or when derived recommendations may be disclosed. Failure and access-change behavior are absent. | Define the principal and authorization boundary at retrieval, reasoning, stored results and delivery; address unknown/denied access, revocation and restrictions carried by derived content. |
| **G4 — Durable state and recovery** | Persisting results and retrying “safely” is insufficient to distinguish a retry from a useful later update or to know what happens after a crash or uncertain delivery. | Define state ownership and transitions, evidence/recommendation identity, redundant-work suppression, attempt/commit boundaries, and recovery for failures and uncertain sends. Include how nightly work is selected and what remains pending for the next run. |
| **G5 — Observable acceptance and dependency order** | “Representative” and “useful, authorized” are not yet a reviewable completion standard. The stages do not explain which contracts must be fixed before downstream implementation. | Identify the representative cases, who judges usefulness, observable authorization/recovery outcomes and the evidence required for handoff. Update sequencing to reflect the resolved design dependencies. Detailed code schemas or a full test matrix are unnecessary at this point. |

These are gaps in the supplied complete draft, not verified defects in an implementation. The review does not supply the missing design or invent system capabilities.

## What can proceed

Known, suitable intake makes narrow intake work technically separable where it relies only on the established contract. That does not make the requested complete design ready, nor should intake progress pre-commit the unresolved downstream contracts. The next useful action is to complete and review G1–G5 before handing off the whole service for implementation. Preserve the existing draft as the baseline for that revision.

This judgment uses only [Case 4](../../../eval-fixtures/concrete-handoffs.md#case-4--handoff-readiness-review). No repository, runtime or live behavior was inspected, and no implementation is authorized by this review.
