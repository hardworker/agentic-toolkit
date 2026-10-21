---
name: self-learning
description: Inspect, explain, or manage the automatic local learning loop that turns Claude and Codex sessions into shared procedures and workflow improvement proposals.
argument-hint: "[status | discover | proposals | feedback | install | disable]"
license: MIT
---

# Self Learning

Normal capture, reflection and recall run through native hooks; no slash command is needed.
Use this skill when the user wants to inspect or manage that loop. Read
[the operating guide](../../docs/self-learning.md) for installation, controls and evidence limits.

Run `python3 <skill-dir>/learning.py status` for health and pending proposals.
Use `context --project <directory> --prompt <task>` to inspect relevant generated skills.
Use `discover --project <directory> [--source codex:<id>] [--source claude:<id>]`
for read-only artifact navigation; `--artifact <id>` preserves an explicit selection within that project.
It returns canonical paths/IDs, revisions/status, supporting-evidence, delivery and reported-outcome
relationships, evidence coordinates and reports. Manual feedback has no invented source-session link.
Listing calls no model, initializes no store and creates no delivery/usefulness receipt. An absent store
returns unavailable; planning does not depend on this runtime. Keep grouping/title metadata in the
planning entry. Use existing artifact IDs for feedback; never move canonical generated artifacts.
Read a proposal before discussing it. Recommend its concrete change with evidence links and a success
condition. A recommendation does not authorize installing the proposed automation.

Generated skills are project-scoped and supplied automatically to both hosts. Keep delivered context,
observed use, and demonstrated usefulness distinct. For explicit user feedback, run
`feedback <artifact-id> --verdict helpful|harmful --note <feedback>`; harmful skills are withdrawn.
Use `dismiss <artifact-id>` when the user rejects a proposal. Do not reinterpret silence as acceptance.
The worker can revise only its own generated artifacts. Edits to existing user/repository skills
remain proposals. Never publish local evidence or make Git remote writes as part of learning.
