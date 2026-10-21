# Named sessions: implementation and controlled pilot

Implemented 21 October 2026. New planning work can use readable session folders while legacy plans and learning artifacts retain their canonical locations. Bulk relocation and live installation are deferred. The [storage contract](../skills/grounded-plan/records.md) gives the commands and ownership rules; [learning discovery](self-learning.md#read-only-artifact-discovery) describes the optional interface.

## Contract

A session entry owns grouping and title independently of source-chat names. Plans keep their existing identities and authority. Creation uses an explicit task key within project scope; continuation uses explicit identity first or one unambiguous saved native-chat association. Titles never merge work. A library lock serializes registration and entry/index updates, and atomic file replacement preserves complete entries. Index failure leaves saved artifacts usable and reports the repair needed.

New plan files and useful evidence can share the session folder without mandatory empty directories. Existing/externally owned files are linked. Physical folder relocation is outside this implementation: deliberate title changes keep the stable folder path. The helper reports the resolved root, respects existing overrides, and never overwrites an explicit output destination.

Discovery reads current and historical evidence, deliveries and reported outcomes without initializing the learning store. A skill supported in A/B and delivered/evaluated in C appears from each with the correct relationship. Explicitly selected canonical links remain selected across refreshes; unattributed manual feedback stays unattributed. Compact entries show a timestamp and recent reports; full evidence and outcomes remain in the canonical learning database/artifacts. Browsing creates neither a model request nor a delivery/usefulness receipt.

## Executed verification

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests -v
git diff --check
```

The 33 tests pass: 19 existing learning regressions and 14 session/discovery tests. The new tests cover project/worktree scope, same-title collisions, explicit/ambiguous continuation, independent titles, simultaneous creation and link registration across processes, canonical ID/path conflicts, legacy-ID lookup, explicit destinations, store overrides, incomplete indexing, symlink ownership, unavailable sources, historical revisions, manual feedback, optional/malformed discovery and isolated installation.

The discovery fixture snapshots every learning-store file before repeated listings and compares hashes afterwards. It also checks absent-store listing creates no directory, unrelated project/session filters return no artifacts, and no `Store` initialization or worker launch occurs. Existing tests retain the original evidence, automatic-feedback eligibility and budget checks. These fixtures use local data and fake model executables; no paid model evaluation is needed for storage or discovery.

Both edited skill frontmatters parse as YAML and retain the repository-required keys; local documentation links, plugin metadata and public-path hygiene pass. The generic skill-creator validator could not run because PyYAML is absent from both available Python runtimes. YAML validation used the system Ruby parser; no dependency was installed.

## Originating-review corrections

The originating chat reviewed the initial implementation commit independently and found two corrections: its suite run passed 32 tests and failed the temporary Git commit under user-enabled signing, and the implementation base lacked the accepted planning refinements through `a532136`. That review did not find a material registration/discovery defect. Its result is separate from the original implementation-environment test pass above.

The fixture now uses command-scoped `commit.gpgsign=false` and an empty `core.hooksPath` for temporary repository initialization, commit and worktree creation. It changes no user/global configuration. The exact documented suite above was rerun without external overrides: **33 tests passed**.

The accepted 0.6.1–0.6.3 changes were applied selectively to planning/review guidance and its public README, architecture, rationale and version history. Purpose-led structure, selective depth, connected explanation and execution-appropriate commitments coexist with the named-session contract. No shared document was replaced wholesale from the branch that lacks self-learning. Session/discovery/runtime code remains unchanged from the reviewed implementation. Grounded-plan is now 0.7.1; the plugin is 1.25.1; self-learning remains 0.2.0.

Verification also checks the integrated guidance against `a532136`, retention of the named-session additions, unchanged self-learning/runtime files, YAML frontmatter, local documentation links, public-path hygiene and whitespace. These corrections are self-checked and ready for originating-chat re-review; they do not establish ordinary-use navigation benefit.

## Temporary-fixture pilot

The controlled pilot creates an existing flat record, links it from a named entry, and adds a fresh plan plus decisive evidence and an observed-result file. It refreshes a canonical learning skill supported in two source chats and delivered/evaluated in a third. Every generated index/entry link resolves; the existing record's bytes and ID remain unchanged. The new plan/evidence share the session folder; the generated skill remains in its runtime store. A separate refresh test records explicit harmful feedback against the canonical artifact ID and observes the withdrawn status on refresh, retaining selected links when a generated file disappears or discovery becomes unavailable.

Observed navigation proxy: index → session entry → plan, decisive evidence or result is two link edges in this fixture, without reconstructing paths from chat history. This is a deterministic accessibility check, not a timed user study. No real-world lookup effort, usefulness improvement, model quality or cost saving has been measured. Temporary fixtures are deleted after verification; no private user artifacts were moved or registered.

## Deployment boundary

The isolated installer test verifies every deployed Python file matches source, both management-skill links remain symlinks, the deployed runtime executes `discover` without changing database contents, and reinstall/uninstall preserve the existing lifecycle. Live runtime copies, hook configuration and management symlinks remain unchanged pending review and authorized rollout. Changing only the management-skill symlink would not deploy the updated runtime.

The originating planning chat independently reviewed the initial implementation and will inspect these corrections. This correction receipt reports source checks and deterministic tests, not an independent review of the corrected commit or ordinary-use validation. Later rollout can observe real navigation effort and preserve explicit feedback; folder migration remains a separately selected operation.
