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

- **Orient first.** State the recommendation, its decisive reason, and any choice blocking progress before background.
- **Adapt the structure.** Architecture, delivery, alternatives, open decisions, and evidence are useful section choices. Combine, rename, or omit them when that helps the reader; preserve material constraints and acceptance conditions.
- **Edit each section.** Start with its conclusion. Keep each paragraph focused on one point and its support. Use descriptive subheadings for topic changes and labeled bullets for distinct rules or conditions; make acceptance and blockers easy to locate separately from rationale. Tables compare; diagrams explain relationships. A dense paragraph moved into one bullet or table cell is still dense.
- **Give each fact one home.** Reference a constraint or decision instead of repeating it across architecture, milestones, and risks. Keep large evidence and review receipts linked; retain qualifications beside the claims they limit.
- **Check usability.** Can a reader find the choice, approach, next action, completion condition, and material uncertainty without reconstructing the investigation? Add detail for a missing answer; remove detail that adds no decision or execution value.

These writing rules apply within the existing skill. Code-level choices remain with the implementer, and evidence and outcome-history requirements remain in place.

## Evidence and limits

A 2026 study compared five ADR templates through author-led feature analysis, then tested Nygard and MADR in a crossover experiment with 33 students. Nygard scored higher on the study's combined measure; feedback also valued MADR's detailed rationale. The measure includes authoring time, consultation, and reported preferences. This is limited support for a depth/overhead tradeoff, not a test of AI plans or an optimum word count. [Paper, methods and limitations][study]

Inspected eight files pinned to commits across five public repositories, plus primary architecture/product guidance and the study's methods, results, and limitations. Checked the documentation against the relevant source instructions, including the reasons for fixed headings. No upstream runtimes, reader trial, or cost benchmark were run; the recommendation is an inference. The 11 October source manifest remains a separate historical snapshot.

### Section readability refinement, version 0.6.1

Real use exposed a remaining problem: paragraphs combined purpose, rules, exceptions, and acceptance conditions despite an organized overall outline. The user clarified that the concern was the sections to read, not total file length.

The refinement makes those concerns separately scannable through topic subheadings, focused paragraphs, and labeled points. It also checks individual text blocks at handoff. One existing private plan was reformatted while preserving its decisions and critical constraints; its contents remain outside this repository. No numeric paragraph limit or mandatory heading set was added. Whether the reader can locate and resolve decisions more easily remains pending feedback.

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
