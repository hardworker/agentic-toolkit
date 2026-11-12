# Case 1 authoring receipt

Produced on 2026-11-12. This receipt records process and verification, separately from the proposed design and plan. Current artifacts after the actual later turn are [case-1-revised.md](case-1-revised.md) and [case-1-revised-design.md](case-1-revised-design.md). The original output records below are retained as initial-turn evidence.

## Source instructions

Read only the assigned pinned authoring files and supplied request packet, followed by this output directory's own artifacts. The request packet was treated as complete, synthetic supplied facts rather than live-system observations. Only case 1 was authored.

| Source | SHA-256 |
|---|---|
| `../brainstorming.md` | `2c9ca71f94886f9ca9f4aef055f7cafb3e1a9bdf3aeebf8f4cb547c69405d207` |
| `../writing-plans.md` | `a6c67c1900064347c2a329990dd3c555657c51c3ec53b259a08aa01a2c26139a` |
| `../../../eval-fixtures/concrete-handoffs.md` | `4595d6a454417fdacf0165bc7bebd4ebc77369820c2510323ac472122853c9c1` |

## Outputs

- [Entry point and implementation plan](case-1.md), 3557 words; SHA-256 `543f9b4b81e800225e1439781951bb4a02088c311c785860c4bab94f52c20535`.
- [Proposed system design](case-1-design.md), 2739 words; SHA-256 `97f14213eb535e4eb4e630d9e0a7727447ff77a11e1ec1e3e68227475ed6ba38`.
- This receipt; no implementation files, source changes or commits were created.

## Checks actually performed

- Builder self-check: checked whether a joining engineer can follow intake, current context, authority/disclosure, bounded reasoning, deduplication, review, delivery and recovery without an architectural decision being deferred. Routine adapter wiring and actual pre-existing filenames remain explicitly unverified.
- Spec coverage: identity/intake → Task 1; context/authority → Task 2; model/tools/cost → Task 3; novelty/concurrency/recovery → Task 4; review/disclosure/delivery → Task 5; useful repository slice/restart/inspection → Task 6; shared inbox/feedback path → Task 7.
- Step and interface scan: seven tasks with five checkbox steps each; named tests, expected outcomes, new signatures and proposed file responsibilities. Commands and assertions are future verification instructions, not claimed executions.
- Review-focus scan: five additional failure classes are assigned to explicit owning-task tests. Authorization includes unquoted context, not only citations.
- Self-review corrections made inline: stable logical evaluation identity and durable call slots across retries; definite refusal releases a slot while uncertain admission retains it; one pending suggestion per authoritative work identity across audiences; intake remains host-only before restrictions resolve; current revision is asserted as structured state; explicit inbox/feedback enablement configuration.
- Static checks passed: required plan header, seven task blocks, five steps per task, design link, named critical acceptance scenarios and Markdown-only output. No behavioral tests were run.
- Proportion check: plan/design word ratio is 1.30; code blocks contain focused assertions, not implementation bodies.

## Upstream process omitted or overridden

The explicit assignment overrides the interactive, execution and storage defaults. Accordingly:

- No questions, conversational approval pause or execution-method choice. Technical alternatives were presented separately before authoring; the recommended approach and all material choices remain labeled proposals rather than accepted user decisions.
- No repository/web recon, external planning-library writes, installations, live setup, model calls or implementation. Proposed integration paths are not presented as inspected existing paths.
- No separate builder agent or other subagent. The required self-check fallback was used; the separate builder prompt was not accessed.
- No browser visual companion, spike or prototype; the design uses a text flow and review-card description.
- Artifacts use the assigned scratch output directory instead of repository `docs/superpowers` locations. No design commit, worktree setup or execution-skill invocation occurred. Local commit steps and the required future execution notice remain in the implementation plan as authoring guidance only.
- Handoff consists of links and limitations, with no interactive approval request or implementation continuation.

## Limitations and blockers

No genuine blocker prevented producing the requested design and plan. No claim is made that the proposed APIs match an inspected source tree, that tests compile/pass, that the model is useful, or that production load/cost targets are known. Existing integration filenames and adapter response shapes require verification at execution. Real-model quality, production volume and an owner-configured budget require separately authorized qualification before enablement. The design explicitly limits cross-source correlation to authoritative resource/task links.


## Actual later turn — inbox first, separate costs and deletion withdrawal

After the initial artifacts were completed, the user supplied this later update through the parent task:

> Start with the shared inbox rather than repository activity. Keep the overall design general across all three source types. Each draft now needs to show its estimated delivery cost, separately from actual investigation spend. If a source item is deleted, pending drafts based on it must be withdrawn before they can be approved or sent. Preserve the individual approval requirement and the rest of the agreed scope. Update the plan so the current decisions, delivery order and acceptance agree; keep superseded decisions out of the main design.

The later supplied source facts were that the delivery adapter exposes a conservative per-message estimate independent of investigation usage, and all three adapters can report deletion/absence on refresh, with deletion events potentially arriving after draft preparation. No live sources were consulted. The same pinned instruction files, scratch-only boundary, no-agent self-check fallback and prohibition on implementation remained in effect.

### Revised current outputs

- [Current implementation plan](case-1-revised.md): 4733 words; SHA-256 `2f5f79ff519899c5af832b00d1bbe62c1a95fd2821b9cb3f77e19559172e174a`.
- [Current proposed design](case-1-revised-design.md): 3729 words; SHA-256 `7576b318e8ddf020a5ee9f3f6c7fe1fba30dc852db549fe673be69b30d24996b`.
- Initial `case-1.md` and `case-1-design.md` were preserved byte-for-byte. Their hashes still equal the initial output hashes recorded above. Only revised files and this receipt were written during the later turn.

### Actual revision work and checks

- Updated the active goal, source order, fixture, allowlist, Task 6 milestone and qualification corpus to shared inbox. Repository activity and feedback follow in Task 7 through the same evaluator. Superseded delivery-order decisions remain only in the preserved initial artifacts/history, not in the current design.
- Defined host-obtained delivery estimates, exact draft/destination binding, separate actual/held investigation accounting and fresh approval on estimate change. No estimate means deferred publication; quote retries with current context do not require another model call. Ledger settlement updates the actual-spend display independently of the approved delivery estimate.
- Added indexed source dependencies/presence generations, immediate deletion observations, transactional withdrawal of review-pending and approved-but-unsent drafts, source refresh before review/approval/send and fences against delayed deletion events. Restored presence requires a fresh authorized read and never revives a withdrawn approval.
- Added acceptance tests for separate cost amounts (`0.02 USD` estimate versus `0.07 USD` investigation actual in synthetic fixtures), unavailable/changed estimates, incomplete settlement, deletion before publication/approval/dispatch, supplementary unquoted source deletion, refresh-only absence, and reconciliation after deletion while a send is uncertain.
- Builder self-check and type/step scan found and corrected the stale-present-read restoration race: a deletion observed during a presence read wins its generation check. Also made `ContextResult` explicitly represent withdrawal and made the review card derive current investigation settlement rather than retain a stale actual-spend snapshot.
- Static checks passed: unchanged original hashes, required header, seven tasks with five checkbox steps each, revised design link, global constraints matching design verbatim, inbox-first milestone, repository/feedback follow-up, no repository-first remnants in current artifacts, separate cost concepts, named deletion acceptance scenarios and Markdown-only output.
- Plan/design word ratio: 1.27. These checks inspect documents, not executable behavior. No product implementation, behavioral tests, source setup, real-model run, install, commit, additional agent or execution-skill invocation occurred.

### Remaining limitations

No blocker prevented producing the revised plan and design. Existing integration paths/APIs, actual model quality and production load/budget remain unverified as in the initial turn. The documents explicitly distinguish enforceable local withdrawal/refresh gates from an absolute atomic guarantee between a remote source deletion and provider acceptance: the supplied adapters do not establish cross-system atomicity. A stronger guarantee covering that remaining interval would require additional provider support; the current acceptance scenarios make no claim to have tested it away. All other approval, disclosure, bounded-cost, retry/deduplication and inspectability requirements are retained.
