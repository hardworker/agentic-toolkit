# Case 1 review revision receipt

Created [case-1-reviewed.md](case-1-reviewed.md) as a separate revision responding to the supplied fresh-reader finding. The overall TypeScript/SQLite service, shared gateway handler, repository-first delivery, source permissions, bounded costs and individual approval architecture are preserved. All five original output files remain byte-for-byte unchanged. This receipt records the revision; it does not revise the original comparison artifacts or the planning skill.

## Corrections made

- Separated historical notification revisions from current mutable source/context state. An old revision remains dated evidence even when it can still be fetched. The proposed current-state read contract requires verification against each owning API; the packet does not establish that capability. Present-tense recommendations defer when their current-state premise cannot be established. Feedback submissions do not acquire invented revision history.
- Added a persisted freshness basis containing mutable facts used by the recommendation, the relevant linked-task query and results, routing basis and local work generation. It includes fields used for action-coverage judgments; task revisions are not assumed. Observation time is audit metadata, not a fingerprint field. Incomplete task retrieval cannot establish that work is unhandled.
- Required authoritative state/task rechecks both when approving and immediately before dispatch, including after quiet hours and before a reconciled retry. Unknown freshness holds an item. A changed basis invalidates approval and schedules the existing bounded handler to reassess. Already-handled work or an obsolete premise retires the draft into an inspectable quiet decision. A regenerated version always needs fresh individual approval, even if its wording is unchanged.
- Preserved provider reconciliation and immutable delivery history. An uncertain prior send must be reconciled before treating the item as unsent, cancelling it or retrying. An unchanged basis after a temporary freshness hold may resume the exact existing approval; an invalidated approval cannot transfer to a new version.
- Added a continuous repository example joining notification revision, current resource state, current work, eligible destination and draft, followed by a covering task appearing before approval or dispatch.
- Updated the reuse table, stage-2 integration prerequisites, planned freshness checks, later-source enablement and remaining verification limits so they agree with the revised design.

## Sources and artifact hashes

No new factual source was introduced. The assigned files below were used for the original authoring and remain the source packet for this revision; paths are relative to `<trial-dir>/`. Their hashes were rechecked during this revision.

| Assigned source | SHA-256 |
|---|---|
| `skill/SKILL.md` | `84ddd48b2d763bbed6f613da477481192e23969b2b3dc0747d60cf6b7c721d47` |
| `skill/plan-template.md` | `548042d87ae5f6bbdfd620ab11bd1704650dd11582f3d00e567e983af374b179` |
| `skill/records.md` | `97e7050a4a434dcba3f4379caf8d197b895f603c2ade3079856619da86fa2949` |
| `requests.md` | `4595d6a454417fdacf0165bc7bebd4ebc77369820c2510323ac472122853c9c1` |

The additional review input was the follow-up task message identifying stale task/source state between reasoning, approval and send. It supplied a design finding, not evidence of a live-system capability. The original Case 1 and this agent's own outputs were the only artifact material inspected for revision; no other review, grader, repository or reference artifact was read.

Hashes of the five originals, recorded before the revision and verified again afterward:

| Preserved output | SHA-256 before and after |
|---|---|
| `../initial/case-1.md` | `e6101bbaa565d2279234e4487bacf6a4eec17926c31cb15843e37c9ac7401ecd` |
| `../initial/case-2.md` | `12b3d2fd28373c788602eae56b58813465eafb19c7b58bfb47f46246806131bd` |
| `../initial/case-3.md` | `448a462f2305970affe264ffd55b016fb4fdd581add80b48b7d993843b634124` |
| `../initial/case-4.md` | `6287e6abac38c22f28d383b2acfa5aa71de5aa605d0178a2b6a29b3bc4fb8797` |
| `../initial/receipt.md` | `03d057fa7ff1835a343a88fcfc87eefdcd3ff71759aae9fe056cdbbb724129f7` |

Final `case-1-reviewed.md` SHA-256: `1b33dee237dd0df959bab457cd70cd7b30c226d3be1886d00f11a6610991f486`. This receipt is not self-hashed.

## Actual checks and limits

1. Read the preserved Case 1, made targeted substitutions into a new file, and inspected the unified diff against the original. Self-checked that the architecture and previously agreed scope remain intact and that the changed design, delivery stages and acceptance scenarios agree.
2. Traced the added example through the before-approval and after-approval/before-dispatch changes, then checked the written rules for unavailable current reads, changed-but-still-useful work, fresh approval, and uncertain prior sends. This was a document walkthrough, not an execution test or independent re-review.
3. Programmatically verified SHA-256 equality for every assigned source and all five original output files. Confirmed the final directory contains exactly the original five files plus `case-1-reviewed.md` and `review-receipt.md`, all nonempty UTF-8 text with final newlines.

No browsing, implementation, external source inspection, other agent, live-library write, model run or interaction with a user approval flow occurred. The added fixtures and behavior checks are planned work; none was executed. Current-state API support, task-query freshness/completeness, semantic action coverage, checkpoint implementation and usefulness remain unverified. The design explicitly retains the race between a successful external-state check and the subsequent provider send; this revision does not claim atomic cross-system consistency.
