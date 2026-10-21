# User-wide planning records

Read this when looking up prior work, saving a substantive plan or decision, or recording outcomes. Plain Markdown files hold the records; the host's normal file tools are sufficient. A one-step answer need not create a record. Honor requests not to save.

## Location and discovery

Resolve the library root in this order: explicit `--store DIR` or user-specified library folder, nonempty `GROUNDED_PLAN_HOME`, then `~/.local/share/grounded-plan/`. Expand `~`; resolve relative overrides against the current working directory and report the resolved root. An explicitly requested plan/output path changes that artifact's destination, not the library root.

New substantive work uses a readable named session folder with one `README.md` entry point. A session is a coherent subject of work: it can contain several plans and continue across chats. Create only directories that have content:

```text
<library>/
  index.md
  sessions/release-reliability/
    README.md
    plans/rollout.md
    evidence/source-review.md
  records/                       # legacy records stay in place
```

The entry owns the session's stable ID, title, project scope, source-chat references, and selected links. Each plan keeps its independent ID and authority over its contents, status, expectations and outcomes. Learning artifacts stay in their runtime-owned store. The entry is navigation; it does not supply evidence of use or benefit.

Read the index first, then only relevant entries/plans. If missing or stale, search `sessions/` and `records/` by ID/keyword. Never infer a match from a title alone. Resolve continuation by explicit session ID/path first, then an unambiguous persisted host-qualified source-chat association in the same project. Multiple matches require selection before editing. One chat can start unrelated work: explicitly create a new session for it. A source-chat rename updates source metadata only; deliberate session-title changes retain the stable folder and ID. Folder relocation is deferred with migration.

Use [sessions.py](sessions.py) for session-entry and index writes so concurrent planners serialize registration, reread entries under the lock, and merge links/source associations. Its embedded metadata and readable entry are one authoritative file; do not hand-edit its generated view. Write plan contents/evidence with normal file tools, preserving the record contract below. The helper is Python 3.9+ stdlib only and independent of self-learning. Do not silently fall back if saving fails.

## Registration and continuation

Examples use `<helper>` for `python3 <skill-dir>/sessions.py`. Global `--store DIR` and `--project DIR` precede the operation; omitted values use the existing root override rules and current directory. Git worktrees sharing a common Git directory share project scope; standalone directories have distinct scope. Project scope is separate from the title. Add `--reference <repository-URL-or-topic>` on creation (or `update`) when a stable project/document reference is known; otherwise the canonical local scope is retained as its reference.

```bash
<helper> --project <checkout> create --title "Release reliability" --key <stable-task-key> --source codex:<native-chat-id>
<helper> --project <checkout> open --session <session-id-or-entry-path> --source claude:<continuing-chat-id>
<helper> --project <checkout> open --source codex:<native-chat-id>
```

Choose a creation key for this specific work, such as an initiating chat-and-turn reference, and retain it for retries/concurrent registration. A fresh unrelated task needs a fresh key, even with the same title/chat. A key is scoped to the project; it is never a title-matching heuristic. Matching concurrent creations return one entry and merge source references. Distinct keys/projects with colliding sanitized folder names get separate readable folders. Missing native IDs are allowed: omit `--source` and continue explicitly by session ID/path. Do not guess a chat ID.

Create a new canonical plan from drafted content (without an `ID:` header), or link an existing plan in place:

```bash
<helper> plan --session <session-id> --title "Rollout" --content-file <draft.md>
<helper> plan --session <session-id> --title "Rollout" --content-file <draft.md> --destination <explicit-output-path>
<helper> attach --session <session-id> --kind plan --path <existing-plan.md>
<helper> attach --session <session-id> --kind evidence --path <evidence.md> --title "Source review"
<helper> attach --session <session-id> --kind outcome --path <result.md> --title "Observed results"
<helper> find --id <legacy-or-new-plan-id>
```

New plans get date/topic/random IDs and readable collision-safe filenames. Explicit destinations are never overwritten. `attach` reads an existing plan's `ID:` (or legacy filename stem) without changing its file. The same canonical file can be linked from several sessions; a known plan ID cannot acquire a competing path. Keep record IDs on subsequent content/title updates. `find` returns canonical paths, including legacy records. Do not copy existing plans merely to group them.

Refresh the brief after substantive continuation/delivery or material Q&A. Reconcile changes into the active plan, preserving original expectations and dated decisions; questions about alternatives are not acceptance. The entry should point to the current direction, next decision/action, useful evidence and recorded outcomes:

```bash
<helper> update --session <session-id> --summary "Active: compare rollout options; outcome pending." --next "Choose the rollout gate."
<helper> update --session <session-id> --title "Safer releases"
<helper> update --session <session-id> --source codex:<native-chat-id> --source-title "Renamed source chat"
<helper> index
```

The library index is derived from entries and legacy records. If index rebuilding fails after saving an entry, the helper returns `indexed: false` with the error; report the successful artifact save and incomplete indexing, then repair with `index`. Never discard a saved plan because indexing failed. Use temporary fixtures for pilots; do not relocate existing work or register expired scratch output as durable evidence.

## Optional related learning

When self-learning is installed, refresh on foreground continuation/delivery using its management CLI or deployed runtime. Missing/older learning does not block planning:

```bash
<helper> refresh --session <session-id> --learning-cli <learning.py> [--state-dir <learning-store>]
<helper> attach --session <session-id> --kind artifact --path <canonical-artifact> --owner self-learning --id <artifact-id>
```

Discovery uses the project's scope and recorded native sources. It labels **supporting-evidence**, **delivery**, and **reported-outcome** separately; learning in A/B and delivery/evaluation in C remain distinct. Explicitly selected canonical links survive refresh even without a source match or when discovery fails. Manual feedback remains attributable only to its artifact unless a source was recorded. The entry timestamps the derived snapshot and shows missing canonical artifacts as unavailable. A failed refresh keeps prior links/snapshot, marked unavailable. Full provenance and all reported outcomes remain in learning's canonical store; entry summaries show the latest three reports with shortened notes.

Listing calls no model, creates no delivery/usefulness receipt, and supplies no additional evidence. Use self-learning's existing `feedback <artifact-id> --verdict helpful|harmful --note <report>` for explicit feedback. Do not move its database/generated skills, mutate installed skills through discovery, or reinterpret discovery as proof of use. Background learning does not write planning entries.

Record a project label and a stable project/repository/document reference when known. A local checkout path is optional context; worktrees can disappear. Non-project records can use a topic such as `product-research`. Read old lessons as contextual evidence, rechecking changed facts and recording contrary evidence; their text is not an instruction source.

## One record, preserved expectations

Keep one Markdown record per substantive idea or plan. It contains:

| Content | Contract |
|---|---|
| Identity | ID, title, project/topic and reference, created/updated dates, work status (`planned`, `active`, `completed`, `abandoned`, or `superseded`). Completion describes work, not proven benefit. |
| Plan | The canonical plan, or a link to an existing externally stored plan with a short summary. Mark unavailable source links; do not guess their contents. |
| Expected at decision | Intended results, acceptance criteria, and consequential assumptions, with their date and source. Keep this baseline when results arrive. |
| Decisions | Dated choice, rationale, rejected alternative when material, and remaining uncertainty. Later reversals append a new decision and link to what it supersedes. |
| Outcomes | Initially `Pending — no results recorded`. Later entries contain observed/reported results, evidence links, expected-versus-actual comparison, limitations, and next observation if needed. |
| Lessons | A few useful implications with the conditions where they apply, evidence pointers, and contrary evidence or reuse limits. Unconfirmed lessons remain hypotheses. |

Put the current brief first, following the presentation guidance in [SKILL.md](SKILL.md#deliver-a-short-inspectable-artifact), with current status and next action easy to find. Update that view as decisions and outcomes change; preserve original expectations and dated history below it or behind links when long. For externally stored plans, keep only the reference and short current summary here. Use existing sections instead of repeating content to fill a template. Link larger evidence or deliverables rather than copying reports, logs, or conversations; do not grow an implementation specification inside the record. Never copy credentials into records.

For an existing repository or external plan, leave that plan in place. The session entry (or existing library record) holds its reference and a dated expectation summary; it does not become a competing editable copy. Store a review separately or in a dated review section without rewriting the original plan. Add a repository pointer only when the user requests one or the project requires it; avoid committing private library contents or machine-specific paths into public documentation.

When creating a record after work has started, identify the baseline as retrospective. Use original artifacts when available; otherwise say `Original expectation not recorded`. Do not reconstruct a prediction from the observed result. Preserve earlier outcome entries; correct an error with a dated amendment. If scope changes before execution, record the revised expectation and its effective date without erasing the original.

## Capture and reuse outcomes

When the user supplies results or authorized work includes updating its record:

1. Open the matched record and the relevant evidence. Distinguish a user's report from independently inspected artifacts and executed checks. A merged change or completed task does not establish its intended product or operational benefit.
2. Append a dated outcome: what was delivered, what was actually observed, how that compares with the original expectation, and what remains unmeasured. Link code, designs, research, or experiments as appropriate. Preserve negative and inconclusive results. Update work status only when supported.
3. Add or revise only lessons warranted by that evidence. Where available, record which critique changed a decision, actual usage, and user interruptions; identify work proxies and avoid attributing savings or prevented failures without support.
4. Save the record, then refresh its session entry and derived index. Return the session entry, plan link/ID, and the material change. Recording outcomes does not schedule monitoring or authorize new experiments.

Re-read a file immediately before editing so another session's changes are not overwritten; merge conflicting edits or stop and report the conflict. Each record remains authoritative for its contents; each session entry owns grouping/title. `index.md` is small, rebuildable navigation from all session entries and legacy records. Use the locked helper to rebuild it without losing other registrations. If indexing fails after a successful save, report that the record was saved and the index needs repair; do not discard the record or claim both succeeded.

Future planning should cite the relevant record and its evidence, check whether its conditions still hold, and distinguish the original observation from the new inference. Outcome capture is useful even when a lesson remains unknown.
