# A substantial plan

A skeleton to adapt, not a form to fill. Keep the order: decision → what exists → design → stages → proof → first slice → what is open. Rename sections to the subject, merge ones that would repeat each other, and drop any with nothing to say. A small request does not use this.

One document is the entry point. The reader should not have to join a requirements file, a research transcript, and a task list to find the chosen solution. When saving through the records helper, leave out the title line; the helper adds it.

````markdown
# <Subject> — <proposed design | implementation handoff | investigation plan>

**Status:** <what this is; what has not been reviewed, run, or approved>
**Sources:** <repository at commit or date; documents; what was unavailable>
**First milestone:** <name>

## Decision

<Two or three sentences: the direction, the decisive reason, and what it deliberately is not.>

<The whole flow in one line or a small diagram.>

> <The immediate goal as one sentence a reviewer could check.>

## Scope

- **Covers:** <…>
- **Not prescribed yet:** <what must be measured or decided first, and why>

| Non-goal | Reason |
|---|---|
| <thing a reader might expect> | <one clause> |

## What exists and what is missing

| Needed capability | Existing mechanism | Reuse, extend, or new |
|---|---|---|
| <capability> | <owner, `path`> | <…> |

Invariants to keep:

- <rule of the current system the change must not break>

Missing:

1. **<Name>** — <one clause on what is absent and why it matters>

## Design

<Overview diagram or ordered flow. Mark what exists and what is proposed.>

### <Concept, named as the project would name it>

<One to three sentences: what is decided and which problem it solves.>

```ts
// only the fields or states that carry a decision
```

Rules:

- <what a value means and does not mean>
- <who may write it; what must never be inferred from it>

Rejected: <the serious alternative> — <why it loses here; the limitation accepted>.

## Stages

### Stage 0 — <result, not activity>

Deliverables:

1. <concrete change or artifact>

Depends on: <…>. Does not yet allow: <…>.

**Exit condition:** <behavior, evidence, or artifact that shows the result>

## Validation and rollout

- <claim> → <scenario, measurement, or artifact that would show it>
- Baselines to measure before any threshold is set: <…>
- Rollback restores: <state and behavior, not only source>

## First slice

<Exact boundary, the stages it includes, what stays outside and why.>

> Given <starting situation>, when <what is done>, then <observable result>, while <condition that must stay true>.

## Deferred

| Left open | Needed by | Settled by |
|---|---|---|
| <decision or value> | <stage> | <measurement, probe, or owner's ruling> |

## Open questions

1. <what is unknown> — affects <stage or decision>; resolve by <…>; blocking: <yes | no>

## Risks

- <risk> — <response>

## Evidence

- **Read in code:** <areas opened, at which commit>
- **Documented only:** <claims that rest on documentation>
- **Not verified or absent:** <what could not be checked, and what would check it>

## Status and next action

<What was read, what was run, who reviewed it and what they changed, what remains unverified. Then the single next action.>
````

## Using the skeleton

**Decision.** Lead with the choice and the picture of the outcome. If the request's literal goal is not the right first goal, say so and restate it.

**Scope.** Non-goals are things a reasonable reader would otherwise expect. "Not prescribed yet" protects against inventing numbers: establish a baseline before a threshold.

**What exists.** Only the behavior and constraints needed to understand the proposal. Distinguish missing functionality from functionality that needs integration or verification. This section should make the amount of new work understandable.

**Design.** One subsection per concept the design turns on: a record with meaningful semantics, a processing stage, a decision policy, a user interaction, an experimental method. Usually three to six. A concept earns a subsection by passing the inclusion test in [SKILL.md](SKILL.md#decide-at-the-right-height); a mechanism that does not pass becomes a row under Deferred. Explain the semantics around a shape instead of treating a code block as the design. For research, the concepts are sampling, measurement, comparison, and analysis choices.

**Stages.** Order by dependency. Near stages are deep enough to start; later stages keep their result, dependencies, and exit condition without internal design. Add owner roles only when coordination matters, without inventing people or commitments. If the brief asks for implementation tasks, decompose the first stage only.

**Validation and rollout.** Separate correctness, usefulness, and operational readiness when they need different evidence. Name real test facilities and commands when known; do not invent existing tests. Omit rollout machinery the work does not need.

**First slice.** The acceptance example should prove the slice's value, not the existence of a component.

**Deferred, open questions, risks.** Deferred items are chosen postponements with a way to settle them. Open questions are unknowns someone must answer. Risks get one line and a response; do not repeat exceptions the design already handles.

**Evidence.** Anchors sit inline, as `path:line`, where the claim is made. This section does not repeat them; it states the reading limits. A long annotated anchor list belongs in a linked evidence file. Re-open each anchor after drafting.

**Sections the request needs.** If the request asks something the skeleton has no slot for, such as a comparison, an inventory, or a what-to-adopt list, give it its own section right after Decision, with each row a decision. The request outranks the skeleton.

**Diagrams.** Use editable Mermaid when relationships are clearer drawn than listed. Keep text and diagram in agreement, and say when a diagram was checked only as text.
