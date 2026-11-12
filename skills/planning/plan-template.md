# A substantial plan

Use this as a working outline, not a form to fill with generic prose. Keep the main progression: recommendation → present situation → proposed solution → delivery → proof. Rename sections to the subject and combine sections that would repeat one another. Omit a section only when it has no useful content. A small request does not need this outline.

The design and the delivery plan belong together by default. Split out large supporting material when necessary, keeping one clear entry point. The reader should not have to join a requirements document, a research transcript, and a task list to discover the chosen solution.

## 1. Recommendation and scope

Open with the chosen direction and the result it enables. State the decisive reason, the most important boundary, and the recommended first milestone. Give the reader a concrete picture of the outcome before introducing its mechanics.

State what this document covers and what is excluded or deferred. Distinguish the overall goal from the first delivery. Label the document's actual maturity: a proposed design, an implementation handoff, or an investigation plan. Do not claim approval or verification that has not occurred.

## 2. Current foundation and gaps

Explain only the existing behavior and constraints needed to understand the proposal. Cite the sources that establish them.

A reuse table is useful when several capabilities already exist:

| Capability needed | Existing mechanism or evidence | Required change |
|---|---|---|
| A capability the solution depends on | Its actual owner and current behavior | Reuse as-is, extend, or add the missing part |

Then identify the gaps the design must close. Distinguish missing functionality from functionality that merely needs integration or verification. Keep important existing invariants visible. This section should make the proposed amount of new work understandable.

## 3. Proposed solution

Start with an overview of how the whole solution works. A flow or component diagram often helps; use editable Mermaid for relationships when useful. Explain the diagram in the text, keep current and proposed elements distinguishable, and check that they agree. Render or syntax-check diagrams when available; disclose when only text was checked.

Give each major design idea its own named subsection. Organize around the subject's concepts: a record with meaningful semantics, a processing stage, a user interaction, a decision policy, or an experimental method. Avoid a flat list of requirements or a paragraph for each implementation file.

Within each subsection, establish:

- **Decision and purpose:** what is being chosen and which problem it solves.
- **Contract or method:** what it receives, produces, owns, and relies on; the rules needed for other parts to use it correctly.
- **Rationale:** why this approach fits, the serious alternative rejected, and the tradeoff accepted. Explain a shared choice once rather than repeating it everywhere.
- **Behavior:** how it participates in the normal flow and what happens in the failures or exceptions that could change the design.

These are content prompts, not four labels to repeat mechanically. Use short explanatory paragraphs, lists of rules, or tables as appropriate.

Define important concepts precisely enough that later stages can refer to them. Use compact record/interface examples when fields, states, or distinctions carry the decision. For instance, an execution result and an assessment of its quality may need separate meanings; merely naming a “result object” would leave that choice to implementation. Explain the semantics around the example rather than treating a code block as the design.

Make interactions concrete. Identify what initiates a flow, which component or person decides, what evidence or state it uses, and where the result goes. For a system, resolve applicable runtime, persistence, lifecycle, authority, and integration choices. For research, resolve sampling, measurement, comparison, and analysis choices. Include only boundaries that matter to this work; do not add a generic safety or reliability catalog.

## 4. Delivery stages

Sequence work by its dependencies and the results it produces. Use a subsection per stage when it needs explanation; a compact table is enough for a short sequence.

Each stage needs:

- **Result:** what becomes possible or known after it.
- **Deliverables:** the concrete changes or artifacts, including their integration with existing work.
- **Dependencies and limits:** what must exist or be decided first, and what this stage does not yet enable.
- **Exit condition:** the behavior, evidence, or artifact that demonstrates the result.

Use responsibility or owner roles when coordination matters, without inventing people's availability or commitments. Put a prerequisite before the work that uses it. A stage that builds records or measurement before a new capability can be valid; say why it is necessary and which later result it enables.

Specify the near-term work deeply enough to start. Later stages retain their intended results and major decisions without speculative coding detail. If the brief asks for implementation tasks, decompose the first stage into bounded work with inputs, outputs, and verification; do not substitute the task list for the design.

## 5. Validation and rollout

Define how the intended result will be judged. Connect claims to representative scenarios, measurements, or inspectable artifacts. Include the consequential failure cases and regressions implied by the design. Name real test facilities and commands when known; do not invent existing tests.

Separate correctness from usefulness and operational readiness when they require different evidence. Establish a baseline before inventing performance, quality, or business thresholds. If a threshold is a requirement, preserve it and explain how to measure it. If selecting it is future work, name the measurement and decision that will set it.

When the change needs staged adoption, explain enablement, observation, and the conditions for continuing, adjusting, stopping, or rolling back. Describe what rollback must restore when state or behavior changes; a generic “revert” is insufficient if it leaves consequential effects behind. Omit rollout machinery when the work does not need it.

## 6. Recommended first slice

Make the immediate commitment easy to find. Name its exact boundary, refer to the stages it includes, and give one concrete demonstration of success. State what remains outside it and why. This is especially useful when the complete design spans several releases or initiatives; merge it into the delivery section when a separate section would repeat the same material.

An acceptance example should identify the starting situation, what is done, the observable result, and any important condition that must remain true. It should prove the slice's value, not merely the existence of a component.

## 7. Open questions, risks, and evidence

Keep unresolved matters specific. For each material question, state what is unknown, which decision or stage it affects, and how to resolve it. Distinguish a blocker from a safe implementation detail or later empirical question. If the current evidence cannot support a required guarantee, say so and give the next investigation; do not silently weaken the requirement.

Explain the important risks and the response to them. Do not repeat every exception already handled in the design. Keep sources near the claims they support; a final evidence section may collect repository anchors and longer research. Close with the concrete next action and any remaining limit on the handoff.
