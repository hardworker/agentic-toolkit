# Planning 0.10.0: concrete design and handoff comparison

12 November 2026. The skill now asks substantial plans to explain the baseline, chosen solution, consequential contracts and behavior, delivery dependencies, and observable acceptance. It permits compact data/state models while leaving routine coding choices to implementation. The default document shape adapts to the subject; research and small reviews remain lightweight. This changes instructions, not the storage helper or execution runtime.

## What was compared

| Method | Frozen authoring source | Cases |
|---|---|---|
| Current | Planning 0.9.2 from toolkit commit `b60a3d11be6ffc25b9a8baf9bbc6835b15f799e9` | Substantial design, small review, product investigation, incomplete-handoff review, then a later design update |
| Candidate | The 0.10.0 instruction revision in this change | The same cases and later update |
| Community | Superpowers [brainstorming](https://github.com/obra/superpowers/blob/22f0b463e7a5e579904dd6211a520321035526f7/skills/brainstorming/SKILL.md) and [writing-plans](https://github.com/obra/superpowers/blob/22f0b463e7a5e579904dd6211a520321035526f7/skills/writing-plans/SKILL.md), pinned to `22f0b463e7a5e579904dd6211a520321035526f7` | Substantial engineering design and implementation plan, then the same later update |

The community comparison exercises both design and implementation-plan authoring, including its complete multi-file output. It does not force the engineering implementation workflow through the small review or research cases; those are proportionality controls on our skill. This is not a comparison with every community method researched earlier.

Three fresh contexts inherited the same parent model settings, with no model override or parent conversation history. Each saw only its assigned instruction snapshot and the [synthetic source packet](eval-fixtures/concrete-handoffs.md). The candidate snapshot was frozen before dispatch. Authoring instructions received no expected answer, grading rubric or output word target. The [reader criteria](eval-fixtures/concrete-handoffs-grading.md) were saved before inspecting outputs.

All methods used the same source/access boundaries: supplied facts only, no browsing or product implementation, no live-library writes, no nested agents, and scratch artifacts only. The user delegated technical choices and requested a completed proposed design and plan without an interactive confirmation pause. Those explicit boundaries override upstream approval, storage and execution defaults; proposals remain proposals. Accordingly this compares authoring under shared restrictions, not complete native skill invocation, interactive interviews, independent-review pipelines or the upstream runtime. Superpowers sources were read from a pinned snapshot, not installed or vendored into the planning skill.

After initial artifacts were saved, each author received the [same requirement update](eval-fixtures/concrete-handoffs-update.md) in a separate turn. It changed the first source to the shared inbox, added estimated delivery cost distinct from investigation spend, and required deletion to withdraw dependent pending drafts. Initial artifacts remain preserved. This exercises an actual later conversational turn rather than putting both requests into the initial packet.

## Results

The candidate produced the kind of substantial design requested, while the small review and research controls stayed proportionate. The current skill also produced a real design: this fixture did **not** reproduce the earlier failure to choose an architecture. The community baseline supplied at least comparable architectural depth and more directly executable failure examples. This supports adopting the clearer instruction contract; it does not establish that the candidate reliably outperforms either baseline.

### Initial engineering handoff

| Method | Observed result | Material limitation or tradeoff |
|---|---|---|
| [Current](eval-results/concrete-handoffs-2026-11-12/current/case-1.md) | Selects the bounded gateway loop, source-independent context and decisions, inherited disclosure restrictions, durable recovery and a full repository-to-approved-delivery slice. | Does not explicitly resolve late older revisions against current source state, or refresh linked work state immediately before delivery. Its authorization recheck alone does not catch newly redundant work. |
| [Candidate](eval-results/concrete-handoffs-2026-11-12/candidate/case-1.md) | Adds explicit current-source reads, distinct delivery/evaluation/suggestion identities, generation and lease rules, durable uncertain-cost handling, and work/source revalidation at approval and delivery. | Longer than current. Refers to a configured gateway admission budget without establishing the aggregate budget's scope or owner; per-evaluation limits are explicit. This capability needs verification or an explicit proposed owner. |
| Community [design](eval-results/concrete-handoffs-2026-11-12/community/case-1-design.md) and [implementation plan](eval-results/concrete-handoffs-2026-11-12/community/case-1.md) | Strong architecture plus concrete generation-race, restart, unquoted-context revocation and uncertain-send scenarios. Defines durable call slots and a background allocation. | File maps, fixture APIs and repeated implementation/test/commit steps add assignment detail and adaptation cost before repository inspection. Some references to existing gateway recovery and idempotent enqueue exceed the supplied facts and should be requirements to verify or add. |

The separate reader provisionally preferred the candidate for a joining engineer because its contracts, first delivery and acceptance were easy to find without prescribing code organization. It found the community set stronger on executable failure examples and potentially preferable for immediate task assignment. These are task-specific judgments, not a ranking by length. The parent checked the consequential passages against the source packet and accepted the two current-version omissions and the candidate's budget-ownership caveat. Original generated artifacts remain unchanged; findings were not silently repaired. The [sealed initial reading](eval-results/concrete-handoffs-2026-11-12/initial-reading.md) uses randomized labels: A = candidate, B = current, C = community. Its initial verdict was saved before the reader received the later update.

All three preserve the broader three-source design, individual approval, current authorization, quiet hours and inspectable outcomes. All choose a host-mediated gateway loop over the less constrained agent runtime for reasons grounded in the supplied capabilities. None equates a schema or component name with the complete design, and none substitutes durable intake for the requested useful delivery.

### Breadth and proportionality controls

Both current and candidate preserve the supplied small documentation plan without inventing an issue or interview. Both investigate the primary 30-day onboarding question, handle incomplete cohorts and uncertain telemetry, separate support anecdotes from evidence, respect opt-in access, and stop short of choosing an unsupported feature. Both reject the incomplete full-design handoff while recognizing independently ready intake. There was no meaningful overall winner on these controls. The current investigation proposes reading original support messages whose access was not supplied; that step should use the summary or remain conditional on permitted access.

The [candidate research output](eval-results/concrete-handoffs-2026-11-12/candidate/case-3.md) and [readiness review](eval-results/concrete-handoffs-2026-11-12/candidate/case-4.md) show why the instruction remains broader than software implementation planning.

### Later requirement update

All three changed the first delivery to the shared inbox while preserving repository and feedback coverage. All distinguish the delivery adapter's estimate from settled investigation usage and unresolved reservations. All carry deletion through prepared drafts, approval, queued delivery and uncertain-send reconciliation, including unquoted dependencies. Superseded repository-first instructions remain in the preserved originals, not the current designs.

The consequential difference is what happens to readiness when a capability is unavailable. The source packet cannot establish atomic ordering between remote deletion and concurrent approval or provider acceptance:

- The [candidate revision](eval-results/concrete-handoffs-2026-11-12/candidate/case-1-revised.md) explicitly gates full approval/delivery on resolving that requirement, names a bounded provider-contract check and its passing criterion, and identifies local guards and investigation work that can proceed independently.
- The [current revision](eval-results/concrete-handoffs-2026-11-12/current/case-1-revised.md) also preserves the requirement and gates its pilot on resolution, with less detailed closure guidance.
- The community [revised design](eval-results/concrete-handoffs-2026-11-12/community/case-1-revised-design.md) and [plan](eval-results/concrete-handoffs-2026-11-12/community/case-1-revised.md) acknowledge the external race and provide strong local deletion checks. However, their operative qualification uses “locally observed pre-dispatch deletion” without explicitly gating live delivery on resolving the stronger requirement or agreeing to narrow it. That leaves a scope/readiness ambiguity; it is not missing deletion handling or concealed uncertainty.

The [revision reader assessment](eval-results/concrete-handoffs-2026-11-12/revision-reading.md), checked against the passages by the parent, prefers the candidate's readiness contract and recognizes the community set's concrete advantages: fencing restoration reads against concurrent deletion, retrying cost estimation without another model call, and updating settled spend without changing the approved message. Cost re-approval policies differ legitimately; the request did not prescribe one. No generated plan was changed after these findings.

### Artifacts and size

The [manifest](eval-results/concrete-handoffs-2026-11-12/manifest.json) preserves instruction and input hashes, normalized/raw artifact hashes, method labels and comparison limits. Apply its zero-context candidate patch to the recorded baseline with `git apply --unidiff-zero` to reconstruct the evaluated instructions. The candidate remained frozen after evaluation; no fixture-specific rules were added to the skill.

| Output, words excluding receipts | Current | Candidate | Community |
|---|---:|---:|---:|
| Initial engineering design and plan | 2,111 | 2,463 | 6,296 across two files |
| Revised engineering design and plan | 3,183 | 3,716 | 8,462 across two files |
| Small review | 99 | 130 | Not assigned |
| Two-week investigation | 1,275 | 1,229 | Not assigned |
| Incomplete-design review | 612 | 572 | Not assigned |

Word counts describe artifact size, not measured effort or quality. The instruction change is 280 net words, from 1,916 to 2,196, with storage guidance unchanged. It adds no mandatory stage, runtime dependency, external skill reference or fixed document template.

## Verification and limits

- YAML/frontmatter and plugin metadata were parsed, and whitespace checked. The bundled validator could not start without PyYAML; its key allowlist also excludes this repository's required `argument-hint`. Validation used Ruby's YAML parser and direct checks of the required fields instead. No dependency was installed merely for this check.
- Archived/raw artifact hashes, word counts, frozen input hashes, relative artifact links, Markdown fences and public-artifact path hygiene were checked. Applying the archived patch to the baseline reproduced the evaluated candidate exactly. The initial reader verdict remained unchanged after the revision review.
- The session helper, storage instructions and installed symlink targets are unchanged. No storage or product runtime tests are warranted by this prose-only change. Behavioral evidence comes from the generated plans and reviews, not assertions over prompt wording.
- Artifact examples are synthetic. The packet supplied many architectural affordances; the trial did not test discovering missing facts in a real repository. Supplied facts were not independently verified against a real system. Planned tests and design walkthroughs are not executed integration checks, model-quality measurements or production qualification. Generated Mermaid diagrams were checked as text, not rendered.
- One initial run per method and one later update do not establish general superiority, reliability or cost savings. Multiple control cases share an authoring context, so they are not fully independent trials. Reader labels can be hidden, but document style can reveal a method. No cross-model or Claude-host comparison was run; token/cost totals are unavailable.
- This comparison used three fresh authoring contexts with two turns each and one separate reader with two turns. These are work counts, not measured costs. It stopped after the requested output comparison and passage audit; no repeat sampling or fixture-specific instruction tuning was performed.
- Upstream process restrictions and instruction-only source isolation limit what the exercise establishes. Shared filesystem access was constrained by instructions, not a separate security sandbox.
