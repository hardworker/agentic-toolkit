# Named sessions and artifact discovery

Proposed **21 October 2026**. This records the design direction; no storage migration or skill/runtime change is implemented here. The detailed planning record and private evidence live in the user-wide library.

## Direction

Use readable session folders for new planning-owned artifacts, and a compact entry point linking all related work. Keep existing or externally owned plans in place. Learning artifacts remain in the learning runtime's canonical store.

```text
<planning-library>/
  index.md
  sessions/
    release-reliability/
      README.md
      plans/rollout.md
      evidence/source-review.md
      artifacts/architecture.mmd
```

The tree illustrates organization, not a required scaffold. Create only useful files and directories. The entry point leads to the current plan, evidence, outstanding decisions, related artifacts, and outcomes.

## Identity and ownership

- A stable session ID groups work; its title and readable folder are presentation. Existing plan IDs remain valid.
- One folder can contain several plans and continue across chats. One chat can also produce unrelated work. Associate artifacts explicitly; never merge by title alone.
- Initialize a session title from the task/chat, then retain it independently of later chat renames. Resolve continuation by explicit identity first, then an unambiguous saved association.
- Keep native source-session IDs and project scope intact. Organization supplies no additional learning evidence.
- The planner owns its session entry and planning artifacts. The learning runtime owns generated skills, proposals, revisions, and reported outcomes. Links connect these stores.
- Preserve explicit output destinations and library overrides. Planning remains usable without learning installed.

## Learning changes

The inspected self-learning runtime already records source sessions, artifact identity, evidence, revisions, deliveries, and outcomes. Its current interface lacks session-oriented artifact discovery. Its generated proposal independently collects two user requests about artifact organization/access; that supports investigating discovery friction, not a claim that the proposed design is effective.

Recommend a read-only discovery operation scoped by project and native source sessions. Return canonical artifact links and IDs, revision/status, and reported outcome evidence. Include supporting-evidence, delivery, and outcome relationships separately: a skill learned in A/B can be delivered and evaluated in C. Preserve explicitly selected links; do not invent a source session for manual feedback. Title/grouping metadata stays with the planning entry, avoiding a second registry.

Grounded-plan refreshes related links when continuing or delivering work and shows the refresh time. The background worker retains its existing write boundary. Naming and listing need no additional model call or reflection loop. Existing feedback and evidence rules remain in force; simply listing an artifact creates neither a delivery receipt nor a usefulness report.

The installed runtime uses a stable copy of its Python files, while the management skill is symlinked. Future runtime changes need installer refresh and verification, alongside the normal skill/documentation updates.

## Rollout

1. Add named session storage and dependable identity/registration for new planning work.
2. Add optional learning discovery and links to canonical outcomes.
3. Pilot indexes over existing records, retaining their current paths.
4. Relocate selected planning-owned records only if useful after the pilot, preserving old references and recoverability.

An index-only rollout is the smallest alternative. The hybrid recommendation also co-locates new work. Moving the learning database or generated skills adds ownership and compatibility work without being required for discovery.

## Acceptance and limits

Verify continuation without duplicate folders, collision handling across projects, concurrent registration, preserved artifact IDs, missing-source reporting, and resolved links. Confirm learning still works without planning metadata, with unchanged feedback eligibility and no model requests for catalog operations. Migration must preserve history, old references, and a recoverable original after partial failure.

Then observe whether users can find a plan, its evidence, and its outcome from the session entry. Navigation checks establish accessibility; actual usefulness requires user evidence. The current investigation inspected local source and used read-only database queries. The proposed layout and integration have not been implemented or behaviorally evaluated.

One fresh source-based critic identified two gaps, both corrected: title authority across multiple chats, and discovery of artifacts delivered/evaluated outside their learning-origin sessions. The parent checked both against source. No review agents executed runtime changes or migration tests.
