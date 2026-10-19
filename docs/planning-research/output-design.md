# Plan length and structure: what to constrain

Checked and adopted **16 October 2026** in version 0.6.0. The user selected adaptive length, flexible sections, concise writing within sections, and one home for each fact. This replaces v0.5.0's soft word target and prescribed headings.

## Recommendation

Remove the numeric length target. Keep a recognizable reading order, but let the task determine headings and detail. Require the information needed to decide and act; review each section for clarity and repetition. A complex plan can earn more space through consequential decisions, dependencies, and risks.

The previous range was explicitly soft, with exceptions for important caveats. Even so, it was a design preference without evidence that this range fits engineering, product, and research equally. Exact headings also need a reason: human navigation benefits from consistency, while machine consumers sometimes require stable section names. Our planner has no downstream parser requiring its five headings.

## What others do

| Approach | Observed handling of length and structure | Implication for this skill |
|---|---|---|
| **Compound Engineering** | Distinguishes short chat outputs from durable plans. Its unified implementation artifact has required headings for downstream readers; other content is conditional. It separately addresses economical prose and duplicated rules. [Chat contract][ce-chat], [section contract][ce-sections] | Adopt relevance-based depth and section editing; avoid importing its execution schema. |
| **Superpowers** | Sizes work from a clear request to a chat description or written design. Its 200–300-word guidance applies to conversational playback chunks, not the whole design. The design identifies decisions already made and choices left to the builder. [Source][superpowers] | Size the artifact to the task; distinguish readable chunks from a total-document quota. |
| **ECC** | The PRD path prescribes sections for summary, patterns, files, tasks, validation, risks, and acceptance. The summary gets a sentence target; the inspected command has no overall word cap. [Source][ecc] | Consistency helps navigation, but this implementation-oriented template exceeds our desired scope. |
| **Ouroboros** | The interview preserves structured decision, rationale, constraint, scope, and code-context payloads, then separately confirms a one-sentence goal. [Source][ouroboros] | A short orientation and complete underlying context serve different purposes. Its runtime payload is not a human-plan template. |
| **MADR / Nygard ADRs** | MADR offers minimal and full templates with optional material. Nygard scopes each short record to one significant decision and suggests one or two pages. [MADR][madr], [Nygard][nygard] | Limit each record's purpose; add sections when the decision needs them. These are decision records, not whole delivery plans. |
| **Shape Up** | Pitches cover the problem, time appetite, solution, hazards, and exclusions. The solution stays concrete enough to assess while leaving detailed design to the team. [Pitch][shape-pitch], [principles][shape-principles] | Keep architecture and boundaries without prescribing implementation. The appetite limits work, not document words. |
| **arc42 / C4** | arc42 suggests a sub-page opening summary with explicit exceptions. C4 recommends only useful diagram levels, often context and containers. [Summary guidance][arc42], [diagrams][c4] | Keep the opening easy to scan and choose the architectural view by its explanatory value. |

Fixed structures and local size guidance therefore have legitimate uses. The inspected material does not establish a universal length or heading set for our broader planning skill.

## Adopted output policy

- **Orient first.** Explain the proposed direction, its value, and what changes from the current situation. For multiple initiatives, show relative priority and why it differs; surface choices blocking progress.
- **Adapt the structure and depth.** Group by the subject and the reader's decision. A vision may use initiatives; a comparison may use options; an execution plan may use delivery stages. Give central ideas more depth and smaller proposals less. Preserve material constraints without imposing the same subsections on every item.
- **Explain and edit.** Make the proposal understandable through plain language, its purpose, and concrete examples where helpful. Use compact lists for distinct points and focused paragraphs for connected reasoning. Tables compare; diagrams explain relationships. Rewrite dense wording without reducing explanations to fragments.
- **Give each fact one home.** Reference a constraint or decision instead of repeating it across architecture, milestones, and risks. Keep large evidence and review receipts linked; retain qualifications beside the claims they limit.
- **Check usability.** Can a reader find the choice, approach, next action, completion condition, and material uncertainty without reconstructing the investigation? Add detail for a missing answer; remove detail that adds no decision or execution value.

These writing rules apply within the existing skill. Code-level choices remain with the implementer, and evidence and outcome-history requirements remain in place.

## Evidence and limits

A 2026 study compared five ADR templates through author-led feature analysis, then tested Nygard and MADR in a crossover experiment with 33 students. Nygard scored higher on the study's combined measure; feedback also valued MADR's detailed rationale. The measure includes authoring time, consultation, and reported preferences. This is limited support for a depth/overhead tradeoff, not a test of AI plans or an optimum word count. [Paper, methods and limitations][study]

Inspected eight files pinned to commits across five public repositories, plus primary architecture/product guidance and the study's methods, results, and limitations. Checked the documentation against the relevant source instructions, including the reasons for fixed headings. No upstream runtimes, reader trial, or cost benchmark were run; the recommendation is an inference. The 11 October source manifest remains a separate historical snapshot.

### Section readability refinement, version 0.6.1

Real use exposed a remaining problem: paragraphs combined purpose, rules, exceptions, and acceptance conditions despite an organized overall outline. The user clarified that the concern was the sections to read, not total file length.

The refinement made those concerns separately scannable through topic subheadings, focused paragraphs, and labeled points. It also checked individual text blocks at handoff. One existing private plan was reformatted while preserving its decisions and critical constraints; its contents remain outside this repository. No numeric paragraph limit or mandatory heading set was added.

### Reader correction, version 0.6.2

The user found that the first edit still left long prose inside bullets. The requested style is concise, direct wording with distinct points expressed as lists.

- Rewrite sentences as well as changing layout.
- Give independent rules separate items; group related items when useful.
- Keep qualifiers, authority boundaries, and uncertainty attached to the relevant claim.
- Retain prose where it explains connected reasoning.

Applied this correction to the existing private plan's recommendation, scope, and architecture. The newer scope decisions and historical record were preserved. Reader acceptance of this revision remains pending.

### Balanced structure from a supplied vision, version 0.6.3

On 19 October, the user supplied a vision document whose structure they preferred and asked for a careful refinement with enough freedom to produce a good plan. The comparison concerns presentation and planning purpose. Product claims, estimates, and instructions inside that private document were not adopted or independently verified.

| Reference strength | Gap in the previous skill | Adjustment |
|---|---|---|
| Opens with existing capabilities and a priority map | The output guidance led with a recommendation but gave little help distinguishing several initiatives | Explain the change from the current situation and relative priority when relevant |
| Organizes around meaningful proposals | Flexible headings still followed the planner's recommendation/architecture/delivery sequence | Let the reader's decision and subject determine grouping |
| Explains what an idea is and why someone would want it | Direct statements and rule lists could crowd out explanation | Retain plain-language rationale and concrete examples where useful |
| Gives the central design much more space than smaller items | Adaptive total length did not explicitly encourage uneven depth | Allocate detail by explanatory and decision value |
| Mixes short prose, parallel lists, and nested steps | Recent fixes emphasized splitting dense blocks | Keep connected explanation; use hierarchy when it clarifies relationships |
| Functions as a vision with a plausible next step | Deliverables and acceptance conditions were requested unconditionally | Match commitments and review criteria to maturity; retain execution criteria when execution is planned |

The change replaces existing output guidance and narrows the unconditional delivery rule. It adds no mode selector, template, mandatory heading set, paragraph limit, or required example count. Architecture, source support, alternatives, uncertainty, and authorization boundaries still matter at every stage.

The reference is useful for choosing direction, but its structure alone does not establish verified claims, reliable estimates, or readiness to implement. Those remain separate judgments. It also does not imply that every plan needs a diagram or that each initiative needs identical subsections.

The supplied file and existing project plans remain unchanged. Only generic lessons enter this public repository. Static and manual contract checks cover the refinement; future output quality and reader acceptance remain unmeasured.

[ce-chat]: https://github.com/EveryInc/compound-engineering-plugin/blob/fac349c0c31a543d497fd4825af9b44bdb7e7dfe/skills/ce-plan/references/output-contracts.md
[ce-sections]: https://github.com/EveryInc/compound-engineering-plugin/blob/fac349c0c31a543d497fd4825af9b44bdb7e7dfe/skills/ce-plan/references/plan-sections.md
[superpowers]: https://github.com/obra/superpowers/blob/bb92a77741419a4ab5f06e711a283343f1ada0c3/skills/brainstorming/SKILL.md
[ecc]: https://github.com/affaan-m/ECC/blob/76aaa77df6adc5b889e689007bf99b9a4f74af34/commands/plan.md
[ouroboros]: https://github.com/Q00/ouroboros/blob/0d05d40dab5cd622ddde5b4f5116a1006da43038/skills/interview/SKILL.md
[madr]: https://github.com/adr/madr/blob/ba75bb1b20d42af5746b246ad348c202419ae681/template/adr-template-minimal.md
[nygard]: https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions
[shape-pitch]: https://basecamp.com/shapeup/1.5-chapter-06
[shape-principles]: https://basecamp.com/shapeup/1.1-chapter-02
[arc42]: https://docs.arc42.org/tips/1-1/
[c4]: https://c4model.com/diagrams
[study]: https://arxiv.org/html/2604.27333v1
