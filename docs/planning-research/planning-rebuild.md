# Rebuilding planning around the handoff

12 November 2026. Planning 0.11.0 replaces the skill body from scratch and adds a substantial-plan outline. The user did not see improvement in 0.10.0. Its synthetic comparison and favorable reader preference were insufficient evidence of the outcome that mattered: a plan with the structure and substance of the supplied engineering handoff.

## What the reference demonstrates

The supplied handoff is useful as a document because its layers are visible:

1. An executive recommendation says what direction to take, why, and where to begin.
2. A reuse map and explicit gaps explain the distance from the existing system to the proposal.
3. The architecture is developed through named concepts, meaningful record examples and the rules around them.
4. Stages have concrete deliverables, limits and exit conditions.
5. Evaluation and rollout explain what would establish benefit and what would permit progression.
6. A recommended first slice gives a bounded commitment and an example of success.
7. Evidence, unanswered questions and review caveats make its maturity inspectable.

Its strength is not its length or the presence of headings. It gives the design room to explain its concepts before turning them into delivery work. The previous trial output often compressed comparable concepts into long paragraphs and a compact milestone table. Checking whether those paragraphs mentioned the right mechanisms did not settle whether the handoff was useful to this user.

The reference is not an instruction to build its proposed system, proof that its claims remain current, or a universal requirement for records, canaries, approval gates or a specific number of stages. Those domain-specific choices are not embedded in the skill.

## Primary-source review and adoption

The [source manifest](planning-rebuild-sources.json) identifies inspected files, content identities and reading scope. The review includes authoring instructions, templates and an actual design artifact. It does not treat repository popularity or marketing claims as evidence of output quality.

| Source | Practice adopted | What is not carried into this skill |
|---|---|---|
| [OpenSpec schema](https://github.com/Fission-AI/OpenSpec/blob/main/schemas/spec-driven/schema.yaml) and [actual update-workflow design](https://github.com/Fission-AI/OpenSpec/blob/main/openspec/changes/archive/2026-10-19-add-update-workflow/design.md) | Distinguish why, required behavior, design choices and delivery; explain decisions with alternatives and rationale; resolve consequential questions before dependent tasks. The actual design demonstrates named decisions and reuse instead of a new subsystem. | Separate mandatory proposal/spec/design/task files, exact scenario syntax, CLI/state machinery and per-edit confirmation. The local plan has one entry point and can combine these layers. |
| Superpowers [brainstorming](https://github.com/obra/superpowers/blob/22f0b463e7a5e579904dd6211a520321035526f7/skills/brainstorming/SKILL.md) and [writing-plans](https://github.com/obra/superpowers/blob/22f0b463e7a5e579904dd6211a520321035526f7/skills/writing-plans/SKILL.md) | Understand existing work before questions; develop the design before tasks; write for a capable builder without the conversation; group setup with the deliverable it serves; check the design as that builder. | Required downstream skills, compulsory approval conversation, exact file/signature prescriptions, repeated test/commit steps and execution-method selection. |
| GitHub Spec Kit [plan command](https://github.com/github/spec-kit/blob/main/templates/commands/plan.md) and [template](https://github.com/github/spec-kit/blob/main/templates/plan-template.md) | Resolve research into decisions with rationale and alternatives; use data models and interface contracts to expose meaningful semantics; describe validation scenarios with expected results. | Constitution/hooks, fixed technology fields, mandatory directory trees and a separate artifact for every concern. |
| [GSD planner](https://github.com/gsd-build/get-shit-done/blob/main/agents/gsd-planner.md) | Work backward from observable outcomes to necessary artifacts and connections; identify dependencies; give work an action, verification and completion condition; permit shared foundations when needed. | Execution waves, XML tasks, context-percentage sizing, provider/tool requirements, fixed IDs and automated checks for every kind of deliverable. |
| [Compound Engineering plan sections](https://github.com/EveryInc/compound-engineering-plugin/blob/4adfcf48ba6279edef75695608b3aa5ed4b6ad58/skills/ce-plan/references/plan-sections.md) | One canonical plan can serve implementer, reviewer and future reader; make design and delivery distinct within it; include sections for actual content; resolve revisions in place; give each rule one authoritative home. | Its full artifact schema, section/requirement/unit identifier registry, executor routing and external writing-skill requirement. |
| [Matt Pocock to-spec](https://github.com/mattpocock/skills/blob/4ae2317ddb22b046e26455e4f9c9b3aaaf62212d/skills/engineering/to-spec/SKILL.md) | Synthesize settled conversation without reopening an interview; keep implementation and testing decisions visible; use existing test seams; include compact snippets when they express a decision better than prose. | Automatic tracker publication, exhaustive user-story requirements and setup dependencies. |
| [Ouroboros plan review](https://github.com/razzant/ouroboros/blob/main/docs/CHECKLISTS.md#plan-review-checklist) | Review whether the proposed work can start soundly, focusing on observable outcomes, costly decisions, deferrals, evidence and reuse. Safe details can remain for execution; a preference is not a demonstrated defect. | Council machinery, host reply contracts, governance and review-quorum rules. |

This is a deliberate adaptation of established planning practices. OpenSpec supplies the separation of purpose, behavior, design and tasks; the reference supplies the readable combined handoff; the other sources strengthen the design-to-delivery connection and builder check. It is not a new planning framework assembled from every source's process.

## Implemented shape

- [SKILL.md](../../skills/planning/SKILL.md) now moves from source grounding to choosing/designing the solution, writing it, checking it as a handoff, and maintaining revisions.
- [plan-template.md](../../skills/planning/plan-template.md) is loaded for substantial plans. Its outline covers recommendation and scope, reusable foundation and gaps, proposed solution, delivery stages, validation/rollout, first slice, and unresolved matters/evidence. It tells the author what belongs in each part and how to develop major concepts.
- The previous scout dispatch, reviewer tiers, blind-alternative debate and call-accounting procedure are removed. One useful fresh review and a targeted follow-up remain optional.
- Small requests, product plans, research plans and early explorations have explicit adaptations. They do not inherit an engineering checklist or forced full template.
- Existing arguments, the canonical-plan/session model, records guidance and storage helper remain compatible. This rewrite changes authoring, not the library implementation.

No upstream planning skill or library is required or named as a dependency in the authoring instructions. Source attribution belongs here. The outline is a starting structure rather than a machine-parsed schema; an existing project or supplied format takes precedence.

## Actual output check

One fresh authoring context received the rewritten skill, its support files and the same [four-case synthetic packet](eval-fixtures/concrete-handoffs.md) used in the previous trial. It did not receive the reference handoff, previous outputs, research rationale or reader criteria. Storage, live research, implementation, nested agents and interactive pauses were disabled for the trial. The author inherited the parent model settings with no override.

The [initial engineering output](eval-results/rebuild-2026-11-12/initial/case-1.md) develops a recommendation and reuse map, then gives separate sections to evidence/work identity, host-owned context and audience selection, decision outcomes, durable execution/budgets, and review/delivery. Its delivery section has four explained stages: durable foundation, a complete repository slice, a measured pilot, and other sources. The first foundation is explicitly not the promised useful delivery.

The [small review](eval-results/rebuild-2026-11-12/initial/case-2.md) preserves the supplied plan. The [research plan](eval-results/rebuild-2026-11-12/initial/case-3.md) develops measurement, interviews, competing explanations, decision rules and a two-person/two-week schedule without turning the work into feature delivery. The [readiness review](eval-results/rebuild-2026-11-12/initial/case-4.md) preserves the deficient draft and separates its architectural gaps from the ready intake work.

The [manifest](eval-results/rebuild-2026-11-12/manifest.json) records input and output identities. Only scratch paths and request pointers were normalized for the archive. The private reference remains outside this public repository. The [reader criteria](eval-results/rebuild-2026-11-12/reader-criteria.md) were written before inspecting the outputs; a separate fresh reader receives the private reference, raw request and anonymized engineering outputs from this trial and 0.10.0. The earlier output is historical evidence, not a newly repeated baseline. There is no new community execution or statistical comparison in this trial.

The [reader report](eval-results/rebuild-2026-11-12/reader-report.md) found the rebuilt output easier to use as a complete handoff: its foundation/change table, named concepts, semantic field and recovery tables, and explained stages make the design easier to follow. It specifically contrasted this with the previous output's paragraph combining supersession, approval races, rejection history, freshness and cross-source suppression. This is primarily a presentation and explanation result, not proof of better runtime design. The labels were A = rebuilt, B = previous; style can reveal a method, so this was label-blinded reading rather than assured blinding.

The same review found a material regression: the rebuilt draft rechecked permissions before sending but did not explicitly recheck whether the work or evidence had become obsolete since drafting. The previous output covered that case. The parent confirmed the gap and requested a separate corrected example, also clarifying current mutable state versus historical notification revisions and adding a continuous walkthrough. The five initial files and instruction snapshot remain unchanged. This exercises the skill's review/revision step; it is not fixture-specific instruction tuning.

The [reviewed example](eval-results/rebuild-2026-11-12/reviewed/case-1-reviewed.md) makes that correction in the design, delivery stages and acceptance cases. Its continuous example follows a repository event through current-state retrieval, task checks, destination selection, a draft, and a task appearing before approval or dispatch. Regeneration produces a new version requiring individual approval. A current-state capability is required and must be verified at integration; it is not claimed as a supplied fact. The [correction receipt](eval-results/rebuild-2026-11-12/reviewed/review-receipt.md) records the checks and limits.

The [targeted follow-up](eval-results/rebuild-2026-11-12/followup-report.md) found that the freshness gap was resolved in the document and the correction remained coherent, conditional on verifying the named source/task-read capabilities. It did not regrade the previous output or the controls. The final reviewed example is not a controlled comparison against the unreviewed historical output.

## Verification

The entry point's YAML/frontmatter was parsed with Ruby, including the repository's required argument hint; plugin and per-skill versions were checked. The bundled skill validator could not start because PyYAML is unavailable. No validation-only dependency was installed. Frozen instruction and archived/raw output hashes, preservation of original supplied text, public-artifact privacy, source/reference paths, Markdown fences and whitespace were checked. References to removed procedures were corrected in the historical documentation without changing its results. No storage-helper or product runtime behavior changed, so no runtime test result is implied. Diagrams were checked as text; a Mermaid renderer was unavailable.

## Limits

Source inspection establishes what practices were adopted, not that those practices guarantee better output. The reference's value is a user preference; an independent grader cannot substitute for that judgment. Generated plans will be inspected for structure, explanation and actionable delivery as well as missing technical decisions. No general quality, cost or reliability improvement is claimed from a single trial.
