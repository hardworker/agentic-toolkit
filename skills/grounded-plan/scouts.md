# Bounded research scouts

Read this only when delegation would help gather evidence. Keep small lookups, tightly coupled reasoning, and cheap local checks in the planner. A scout is useful for compressing bulky material or investigating a separable question; parallel tool calls are often enough for simple retrieval. If delegation is unavailable, research directly and state material coverage gaps.

## Dispatch

Use the smallest useful assignment. Default to **at most two scout calls total, including follow-ups**, unless the user sets a different research budget. This cap is separate from review calls and does not reset between research rounds. No recursive delegation. Lean mode does not require scouts; deep mode does not automatically add them.

Give each scout:

- One decision-relevant question and the constraints needed to answer it, without prescribing the conclusion.
- A distinct source/search scope, relevant paths or URLs, and a stop condition. Prefer pointers over the conversation history. Do not assign overlapping searches unless deliberately checking a disputed claim.
- Permission to inspect sources and perform specified non-destructive checks, with writes limited to designated scratch evidence. No implementation, external mutations, or further agents.
- A compact return budget, usually 300–500 words, with larger evidence linked when needed. Never omit a consequential caveat just to fit it.

Inherit the available model by default. Use a cheaper available model for bounded extraction only when authorized and adequate; do not require a weaker model for difficult investigation or set up a paid provider to fill the role. Continue independent work while scouts run, without repeating their search.

## Return and reconcile

Request an evidence packet, not a second full plan:

| Field | Content |
|---|---|
| Finding | Answer and decision-relevant claims labeled observed, tested, inferred, assumed, or unknown |
| Evidence | Source URL or file/line, version/commit or retrieval date where relevant; actual check command, result, and limits |
| Challenge | Contrary evidence, competing interpretation, and source disagreement |
| Gap | What remains unknown and the cheapest next observation; links to larger evidence if needed |

The planner opens the underlying evidence for claims that decide the recommendation, inspects contradictory evidence, and resolves material inconsistencies. Check a suspicious or consequential result through the cheapest useful channel; do not automatically rerun every check or repeat the whole investigation. Inaccessible support remains an explicit gap. Attribute checks run by a scout; do not report them as personally executed.

Two scouts citing the same origin do not corroborate each other. A scout report is evidence input, not independent proof, and its author cannot serve as the fresh critic of that same work. Follow [review.md](review.md) separately when critique is warranted.

Record scout calls, checked evidence, remaining gaps, and why research stopped in the verification receipt. If the cap is reached, finish the supported parts and expose any consequential gap; do not silently add agents or claim complete coverage.
