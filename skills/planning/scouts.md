# Bounded research scouts

Use scouts for bulky sources or separable questions; keep cheap lookups and tightly coupled reasoning in the planner. Direct research and parallel tool calls are the default. If delegation is unavailable, research directly and expose material coverage gaps.

## Dispatch

Default to **at most two scout calls total, including follow-ups**, unless the user sets another research budget. The cap spans research rounds and is separate from review; increased scrutiny does not reset it. No recursive delegation.

Give each scout:

- One decision-relevant question, necessary constraints, distinct source scope and stop condition. Avoid overlapping searches unless checking a disputed claim.
- Read-only source access and specified non-destructive checks; writes only to designated scratch evidence. No implementation, external mutations or further agents.
- A compact evidence packet, usually 300–500 words, linking larger material without omitting consequential caveats.

Inherit the available model. Use a cheaper model only when authorized and adequate; do not install a provider or require a weaker model. Continue independent work while scouts run.

## Return and reconcile

The packet contains findings with evidence status, source/version pointers, executed checks and limits, contrary evidence, remaining gaps and the cheapest useful next observation.

Open the underlying sources for decisive claims and resolve material contradictions. Verify consequential or suspicious results through the cheapest useful check; do not repeat the whole investigation. Attribute scout-run checks and label inaccessible support as a gap.

Two scouts repeating one origin do not corroborate it. A scout cannot be the fresh critic of its own work; follow [review.md](review.md) separately when needed.

Record scout calls, checked evidence, gaps and the stop reason. At the cap, deliver the supported conclusion with its limits; do not silently expand the budget or claim complete coverage.
