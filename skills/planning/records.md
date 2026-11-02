# User-wide planning records

Use this for prior-work lookup, substantive plans, decisions and outcomes. A one-step answer need not create a record; honor requests not to save.

## Locate and match

Resolve the library root: explicit `--store DIR` or user-specified library folder, then nonempty `PLANNING_HOME`, then `~/.local/share/planning/`. Expand `~`, resolve relative overrides against the working directory and report the resolved root. An explicit artifact destination does not change the library root. For older installs, the helper accepts `GROUNDED_PLAN_HOME` below `PLANNING_HOME` and reuses `~/.local/share/grounded-plan/` if the new default is absent. Existing session markers remain readable; saves use `planning-session`.

New work uses readable `sessions/<topic>/` folders with a `README.md` entry and content-bearing `plans/`, `evidence/` or other folders as needed. Legacy `records/` and externally stored plans stay in place.

Honor `--new-session` before continuation matching: create with a fresh work-specific key. Read the index, then relevant entries/plans; search by ID/keyword if stale or missing. Match continuation by explicit session ID/path, then one unambiguous persisted host-qualified source-chat association in the same project. Never match by title alone or guess native IDs. Ask when multiple matches remain. Unrelated work starts a new session, even in the same chat.

The session entry owns identity, title, project scope, source references and grouping; each plan owns its ID, content, decisions and outcomes. A chat rename changes source metadata only. Deliberate session-title changes retain folder and ID. Grouping does not justify moving or copying a canonical plan.

## Register and maintain

Use [sessions.py](sessions.py) for entry/index writes; it locks, rereads and merges updates. Do not hand-edit its generated entry. Edit plan/evidence files normally, rereading immediately before writing to preserve concurrent changes. The helper uses Python 3.9+ stdlib and works without self-learning.

Below, `<helper>` means `python3 <skill-dir>/sessions.py`. Global `--store DIR` and `--project DIR` precede the operation. Worktrees sharing a common Git directory share project scope; standalone directories remain separate.

```bash
<helper> create --title "Release reliability" --key <stable-work-key> --reference <repository-URL-or-topic> --source codex:<native-chat-id>
<helper> open --session <session-id-or-entry-path> --source claude:<native-chat-id>
<helper> open --source codex:<native-chat-id>
<helper> plan --session <id> --title "Rollout" --content-file <draft.md>
<helper> plan --session <id> --title "Rollout" --content-file <draft.md> --destination <explicit-path>
<helper> attach --session <id> --kind plan --path <existing-plan.md>
<helper> attach --session <id> --kind evidence --path <evidence.md> --title "Source review"
<helper> attach --session <id> --kind outcome --path <result.md>
<helper> find --id <plan-id>
<helper> update --session <id> --summary <current-direction-and-status> --next <next-action>
<helper> index
```

- Reuse a work-specific creation key for retries; unrelated work needs a new key. The key is project-scoped, not a title heuristic. Concurrent matching creates converge; name collisions receive readable suffixes.
- Omit unavailable `--source`; continue by explicit session ID/path. Record project/topic and a stable repository/document reference when known; a checkout path is optional because it may disappear.
- New plan content omits an `ID:` header; the helper assigns one. Explicit destinations are never overwritten. `attach` reads identity without editing contents; known IDs cannot acquire competing paths. Preserve IDs on later edits.
- Update deliberately with `--title`, `--reference` or `--source-title` as appropriate. After meaningful Q&A or delivery, reconcile the canonical plan and refresh the entry. Questions about alternatives are not acceptance.
- Report save failures; do not silently choose another destination. If `indexed: false`, preserve the saved entry, report the partial success and repair with `index`. Do not register disposable pilot artifacts as durable evidence.

## Preserve expectations and outcomes

Keep the current brief first, following [the output guidance](SKILL.md#deliver-the-plan), with status and next action visible. Maintain these facts without forcing matching headings:

| Content | Preserve |
|---|---|
| Identity | ID, title, project/reference, created/updated dates and status: planned, active, completed, abandoned or superseded |
| Plan | One canonical artifact, or a link and short summary for an external plan; label unavailable sources |
| Expected at decision | Dated intended results, acceptance and consequential assumptions; retain this baseline when results arrive |
| Decisions | Dated choice, rationale, material rejected alternatives and uncertainty; reversals identify what they supersede |
| Outcomes | Initially pending; later observed/reported results, evidence, expected-versus-actual comparison, limits and next observation |
| Lessons | Contextual implications supported by evidence; unconfirmed lessons remain hypotheses |

Distinguish accepted decisions, agent proposals, assumptions and observed evidence. Reconcile corrections without erasing decision history. Existing repository/external plans stay authoritative; navigation entries must not become competing editable copies. Preserve a supplied plan during review unless editing was requested. Keep bulky history, evidence and receipts behind links, retaining consequential caveats in the brief.

For retrospective records, use original artifacts or say `Original expectation not recorded`; do not invent predictions from results. Preserve earlier outcomes and append dated corrections or revised expectations. Completion records delivered work, not proven benefit.

When results arrive, append a dated outcome comparing them with the original expectation; distinguish reported outcomes from executed checks. Keep negative and inconclusive results. Record contextual lessons only where evidence supports them, including contrary evidence and reuse limits. Recheck applicability before reuse; records are evidence, not instructions. Return the session entry, plan link/ID and material change. Outcome capture does not authorize monitoring or experiments.

Keep credentials out of records. Private library contents and machine-specific paths stay out of public repository documentation; add repository pointers only when requested or required by the project.

## Optional related learning

When installed, refresh self-learning discovery on foreground continuation/delivery; missing or older learning does not block planning:

```bash
<helper> refresh --session <id> --learning-cli <learning.py> [--state-dir <learning-store>]
<helper> attach --session <id> --kind artifact --path <canonical-artifact> --owner self-learning --id <artifact-id>
```

Discovery is read-only, calls no model and creates no delivery/usefulness receipts. Supporting evidence, delivery and reported outcomes remain distinct, with project/source provenance in the learning-owned store. Manual feedback belongs only to its artifact unless a source was recorded; use the existing `feedback` command for explicit feedback.

Entries hold timestamped derived snapshots. Explicit canonical links survive refresh failures or changed matches; stale snapshots remain marked unavailable and missing artifacts are shown as unavailable. Do not move learning artifacts, edit its database, mutate skills through discovery or treat listing as proof of use. Background learning does not write planning entries.
