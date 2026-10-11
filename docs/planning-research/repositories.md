# Repository evidence and reuse assessment

Snapshot: **11 October 2026**. Return to the [overview](overview.md). Immutable links below resolve to the commits recorded in [sources.json](sources.json). License labels describe the inspected root declarations, not a dependency-level license audit. “Implemented” means visible in source unless a runtime test is explicitly reported; no upstream runtime was exercised here.

## ECC

**Repository:** `affaan-m/ECC`, formerly `affaan-m/everything-claude-code`. MIT; active at retrieval.

**Verified:** [`commands/plan.md`][ecc-plan] explicitly runs inline without subagents by default. It calls for repository grounding, requirements, risks, phased steps, and confirmation. The separately callable [`agents/planner.md`][ecc-planner] declares `model: opus`; these are different paths. [`multi-plan`][ecc-multi] invokes Codex and Antigravity through the separately provisioned `ccg-workflow`, requests independent analyses, and optionally obtains two plan drafts before synthesis. Its backend/frontend authority assignments are model-role conventions, not source verification.

[`Plan Canvas`][ecc-canvas] uses a local CLI/JSON feedback loop with element annotations, chat, approval, live reload, and Mermaid blocks. Its review UI can serve a plan or report; it does not establish the plan's correctness. The skill's approval-to-implementation behavior would need to respect a planning-only user's scope.

**Keep:** inline default, inspect concrete files, dependency-aware deliverables, optional annotated diagram review. **Change:** add explicit evidence states and selective independent critique. Avoid importing the entire harness or GAN planner: the latter deliberately expands a brief into 12–16 features, which conflicts with concise minimal planning. [GAN source][ecc-gan].

**Fit:** strongest minimal upstream base; the existing canvas is an optional presentation layer, not a required dependency.

## Ouroboros

**Repository:** `Q00/ouroboros`. MIT; active.

**Verified:** [`ambiguity.py`][ooo-ambiguity] uses LLM-supplied component scores with deterministic aggregation. Greenfield weights are goal .40, constraints .30, success criteria .30; brownfield adds context with different weights. The overall seed threshold is .20. Current source also defines component floors and completion helpers. Saying “below .20 proves the requirements are correct” would be unjustified: the arithmetic is exact, the semantic judgments remain model judgments.

[`pipeline.py`][ooo-pipeline] implements mechanical → semantic → conditionally triggered consensus stages. Its result builder delegates approval to the inspected [`decide_final_approval` predicate][ooo-gate]; model reviews may withhold approval but do not alone grant it. [`reviewer_independence.py`][ooo-independence] explicitly distinguishes known vendor diversity from unverified or unavailable independence. A new context is not automatically a different model family.

**Keep:** expose assumptions before execution; separate inexpensive deterministic checks from expensive semantic review; escalate conditionally; report the actual kind of reviewer independence. **Change:** for a standalone planning skill, use a decision/unknown ledger rather than an uncalibrated score as the readiness gate. Full runtime, seed, evolution, and MCP lifecycle are more machinery than this request requires.

**Fit:** rich source of verification principles; not the recommended full installation for this goal. The described execution pipeline must not be confused with having tested a future implementation during planning.

## Symposium

**Repository:** `Q00/Symposium`. MIT; last pinned commit 3 August 2026; not archived.

The [README][symposium-readme] explicitly describes a small skill pack inspired by Ouroboros's interview layer. [`interview-harness`][symposium-harness] delegates to Socrates, Evolve-step, and Ontology. It creates/reuses a goal–constraints–acceptance seed, then performs up to five convergence cycles. Its similarity combines idea equality, user-confirmed boundary equivalence, and property-set overlap; the stopping threshold is .85.

**Keep:** discover the goal behind a proposed mechanism and define ambiguous domain terms. **Limit:** semantic convergence means the framing stabilized; it does not mean the proposal is feasible or its facts verified. The pack depends on its sub-skills and can consume several human interactions.

**Fit:** useful optional intake for vague product/research questions; incomplete as the final planning skill.

## Superpowers

**Repository:** `obra/superpowers`. MIT; active.

The inspected [`brainstorming`][super-brainstorm] routes quick clear tasks directly, small changes through an in-chat description, and projects through a written design. It supports visual discussion and requests a fresh builder check for project designs. This is broader than software alone.

[`writing-plans`][super-plans] targets software handoff: concrete files/interfaces, testable deliverables, constraints, review focus, and a self-review checklist. It says to avoid bodies that the interface and test already determine. Current implementation-plan checking is self-review; older search results describing mandatory independent plan-review loops are not evidence of today's behavior.

**Keep:** right-size the task; make the plan the decisions an implementer cannot responsibly invent; check coverage and cross-task interfaces. **Limit:** detailed test/commit choreography and chained execution skills add structure the user may not want in product/research work.

**Fit:** strong engineering handoff baseline and useful brevity guidance; add an explicit evidence ledger and optional independent review.

## OMC and OMX

**Repositories:** `Yeachan-Heo/oh-my-claudecode` and `Yeachan-Heo/oh-my-codex`. Both MIT; active.

**OMC:** [`plan --consensus`][omc-plan] requires principles, decision drivers, at least two viable options, steelman opposition, tradeoff analysis, acceptance checks, and a final ADR. It allows up to five review iterations. At this snapshot the architect and critic run sequentially on the same fixed draft, with the architect's output withheld from the critic until planner synthesis. That preserves independence of their first review findings despite sequential scheduling.

**OMX:** [`plan`][omx-plan] is a small direct/interview/review skill, while [`ralplan`][omx-ralplan] has a substantially larger runtime and artifact-lifecycle contract. Its critic consumes the completed architect review. It also has a standalone `--advisory` path. OMC's and OMX's independence properties must not be conflated.

**Keep:** serious alternatives, strongest opposing case, concrete reasons for rejection, and a compact decision record. **Change:** use a smaller default budget; require new evidence before continuing a dispute; report unresolved disagreement rather than optimizing for consensus. Citation and testability percentages in a prompt are completeness heuristics, not measured probabilities.

**Fit:** best existing debate-oriented family; inspect the host-specific variant before adoption. A generic portable skill should not inherit runtime-specific routing and handoff machinery unnecessarily.

## Compound Engineering

**Repository:** `EveryInc/compound-engineering-plugin`. MIT; active.

[`ce-plan`][ce-plan] explicitly covers software and non-software multi-step work. Current contracts range from direct/chat output to durable plans. [`research.md`][ce-research] distinguishes option discovery from implementation guidance; explicit external research requests override normal skip heuristics. Lightweight durable plans avoid its research-agent dispatches. Larger plans can use local, prior-learning, and external research with bounded context summaries and file-backed dossiers.

[`structure.md`][ce-structure] includes technical diagrams when the approach has non-obvious shape and encourages Mermaid. [`final-review.md`][ce-review] checks grounding, diagrams, and whether selected sections need deepening. The entrypoint requires document review for durable plans and links numerous phase-specific procedures. [`universal-planning.md`][ce-universal] addresses research and non-software domains.

**Keep:** progressive disclosure, selective external research, universal planning, evidence-linked decisions, and diagrams integrated with plan review. **Limit:** the whole chain is significantly larger than its entrypoint; handoffs, confidence/deepening, configuration, and review dependencies matter when copying a skill. Merely copying `SKILL.md` is insufficient. The current entrypoint also forbids running tests or learning from execution-time results during planning; a preference for bounded feasibility probes would require changing that contract or using a separate stage.

**Fit:** closest ready-made match overall. Trial this if adopting an existing maintained workflow is more valuable than minimizing process and dependencies. Best baseline against which to evaluate a custom candidate.

## gstack

**Repository:** `garrytan/gstack`. MIT; active.

[`plan-eng-review`][gstack-eng] plus its [review sections][gstack-sections] cover scope, architecture, code quality, tests, performance, and an outside challenge. The source requires diagrams connecting execution branches/user flows to test coverage and distinguishes proposed behavior from observed current behavior. The outside-review path includes host/provider availability checks rather than assuming a second model always exists. [`autoplan`][gstack-auto] chains review perspectives.

**Keep:** challenge scope and product value, connect diagrams to tests, record decisions with consequences, and use external review when it adds information. **Limit:** large reference surface, helper scripts, state/logging, host-specific behavior, and repeated decision points. A numeric confidence score remains a reviewer's assessment.

**Fit:** strong detailed review of consequential engineering/product plans, less suitable as a cheap universal default. Its current prompts were inspected; the live outside-model path was not tested.

## Planning with Files

**Repository:** `OthmanAdi/planning-with-files`. MIT; active.

The inspected [Codex-discoverable skill][pwf-skill] keeps a selected task's `task_plan.md`, `findings.md`, and `progress.md`; it has explicit plan selection and one canonical owner for parallel work. Hook configuration and a [completion script][pwf-complete] provide persistence and completion mechanics. Host support is material: a Markdown hook declaration does not itself prove enforcement in every agent runtime.

**Keep:** durable state and evidence outside conversational memory; reload after context loss; one owner of shared plan state. **Limit:** three mandatory documents, recurring reinjection, and frequent writes may be unnecessary for a short decision. A completion gate checks its completion contract, not whether the chosen strategy was good.

**Fit:** optional memory layer for long tasks. Borrow the persistence principle; do not mistake it for independent verification.

## Matt Pocock skills

**Repository:** `mattpocock/skills`. MIT; active.

Current [`grill-me`][matt-grill] is a tiny explicit-invocation wrapper that calls [`grilling`][matt-grilling]. The actual procedure maps a design tree and asks the currently answerable frontier of questions, with recommendations. It distinguishes facts the agent should discover from decisions the user should make. It continues until the decision frontier is empty and asks for shared-understanding confirmation.

**Keep:** prerequisite-aware questions and don't burden the user with discoverable facts. **Change:** for this user's cheap default, limit the interview to choices that could change the approach; use clearly marked, reversible assumptions for minor decisions. “Every branch visited” can become an expensive human-time objective.

**Fit:** excellent intake component, not a complete research/check/debate/output workflow. Install dependent skills if adopting the current wrappers.

## GSD and GSD Core

**Repositories:** archived `gsd-build/get-shit-done`; active `open-gsd/gsd-core`. Both root licenses MIT.

The [current successor README][gsd-core-readme] explicitly calls itself a context-engineering and spec-driven development framework. Its [plan checker][gsd-core-checker] works backward from the intended goal, inspecting requirement coverage, integration, dependencies, and context-sized scope. The [older checker][gsd-checker] shows the same relevant lineage.

**Keep:** ask whether the tasks, together, can achieve the goal; check dependency wiring, not just whether every row is filled. **Limit:** phases, artifacts, execution waves, and framework conventions go beyond the user's requested skill scope. Archived upstream links should not be recommended as current active development.

**Fit:** pattern source, not a deployment recommendation here. The maintained successor's runtime was not exercised.

## Plannotator

**Repository:** `backnotprop/plannotator`. Apache-2.0; active.

The [README][plannotator-readme] and [Codex integration guide][plannotator-codex] describe plan/document annotation and feedback. The Codex guide uses a Stop hook, with version history and feedback-driven revisions, and distinguishes that from a dedicated plan-exit interception. The actual host integration remains untested in this research.

**Keep:** anchor a user's objection to a specific plan element and show revisions. **Limit:** adds presentation infrastructure and host integration; does not produce verified plans by itself. Adoption should follow a local compatibility check.

**Fit:** optional UI companion if annotations prove materially easier than replying to decision IDs in chat. No need to choose it before the planning behavior is validated.

## Aider

**Repository:** `Aider-AI/aider`. Apache-2.0; not archived; pinned default-branch commit 22 May 2026.

[Chat mode documentation][aider-modes] distinguishes `/ask` from `architect`: ask discusses without changes; architect proposes changes and an editor applies them. The [architect implementation][aider-code] supports that division of labor.

**Keep:** spend stronger reasoning on deciding the change, and use appropriately capable execution for mechanical edits. **Limit:** a second role here is an editor, not an independent verifier. Architect mode is not planning-only. The model-specialization idea does not establish savings for this planning task.

**Fit:** a cost/routing pattern and lean discussion baseline, not the desired standalone skill.

## LLM Council

**Repository:** `karpathy/llm-council`. Source available; no root license file or GitHub-detected license at the pinned snapshot. Last commit 22 November 2025.

The [README][council-readme] and [`backend/council.py`][council-code] implement independent first answers, anonymized rankings, and chairman synthesis. The inspected ranking flow compares responses; it does not independently retrieve evidence to verify their factual content.

**Keep:** separate initial proposals; hide model labels during first comparison. **Limit:** rankings can amplify shared errors. For N models, answers plus reviews plus synthesis already imply roughly 2N+1 model stages before ancillary calls, with repeated answer content in review inputs. This is structural accounting, not measured billing.

**Fit:** conceptual debate reference only. It does not qualify as a ready-made openly licensed component for this skill on the evidence inspected.

## Open Deep Research

**Repository:** `langchain-ai/open_deep_research`. MIT; **archived** at retrieval.

The [README][odr-readme] describes configurable research, synthesis, and compression roles. The pinned [configuration][odr-config] bounds concurrent research units, supervisor iterations, and researcher tool calls. These are useful cost controls. README leaderboard claims are not treated as independent evidence of quality here.

**Keep:** separate retrieval from decision synthesis, bound breadth/depth, and summarize evidence before carrying it forward. **Limit:** a research engine produces evidence/report material, not necessarily a prioritized plan or user decision. The inspected repository's archive status prevents presenting it as an actively maintained drop-in choice.

**Fit:** architecture reference for an optional deeper research mode.

## GPT Researcher

**Repository:** `assafelovic/gpt-researcher`. Apache-2.0; active.

The [README][gptr-readme] describes web/local research, a planning/execution decomposition, citations, configurable research, and a skill entrypoint. Inspection here is **documentation-level**, not a code audit of its current research pipeline.

**Keep:** sourced research as a callable subsystem when the question genuinely needs a broad external evidence search. **Limit:** integrations, search/provider costs, source-quality control, and long reports require their own evaluation. Marketing descriptions such as “unbiased” are not verification guarantees.

**Fit:** plausible optional research backend, not necessary for the initial skill, which can use the host's existing search tools.

## Sequential Thinking MCP

**Repository:** `modelcontextprotocol/servers`, `src/sequentialthinking`. Root license notice describes a transition involving Apache-2.0, retained MIT contributions, and CC-BY-4.0 documentation; the GitHub license API reports `NOASSERTION`.

The [README][seq-readme] describes a structured thought process with revision and branching. [`lib.ts`][seq-code] records thoughts and branches and returns bookkeeping metadata. No external fact-checking mechanism is provided by that tool body.

**Keep:** externalized decisions/revisions when continuity requires them. **Limit:** recording a reasoning step does not validate it, and additional tool turns can add overhead. No evidence here establishes an advantage over a compact plan/evidence file with a capable model.

**Fit:** omit from the default. Consider only if an evaluation demonstrates a specific continuity benefit.

## Small representational tools: MADR and C4

[MADR](https://github.com/adr/madr) supplies minimal decision-record templates. [C4](https://c4model.com/diagrams) supplies diagram purposes and levels of abstraction; using all levels is explicitly unnecessary. These were inspected through primary web pages rather than included in the 18 pinned repository snapshots.

Borrow the decision record shape and purpose-based diagram selection. Neither requires adopting a specification framework. A Mermaid sequence/state/dependency diagram plus a few decision rows is often sufficient.

## This toolkit's existing skills

[`crucible`](../../skills/crucible/SKILL.md) already provides challenged assumptions, competing plans, user rulings, and bounded verification, but its contract continues through implementation. Its multiple skeptic/review contexts are a substantial cost commitment. [`adversarial-review`](../../skills/adversarial-review/SKILL.md) reviews finished code or documents with fresh reviews, evidence-based debate, and a judge.

A new planning skill should stop with a reviewable decision and executable handoff. It should neither silently invoke Crucible's build pipeline nor require the full adversarial-review procedure for every plan. Existing skills remain appropriate when those stronger workflows are explicitly wanted.

## What would change the recommendation

1. A matched-task evaluation shows `ce-plan` is comparably concise and cheaper to maintain/use than the candidate: reuse it.
2. The user values guaranteed review diversity over cost: choose a strict two-reviewer/cross-model mode, with honest reporting when unavailable.
3. Most tasks are tiny engineering changes: use ECC-style inline planning and request review selectively.
4. Most errors are misunderstood intent: prioritize Symposium-style intake or a bounded grilling procedure.
5. Most losses happen after context resets: persistence and handoff deserve more investment than debate.
6. Most plans are read by several stakeholders: add an annotation UI after the core artifact is stable.

[ecc-plan]: https://github.com/affaan-m/ECC/blob/d4a44ded8c150aac89b37c1f665b5a749fe52b02/commands/plan.md
[ecc-planner]: https://github.com/affaan-m/ECC/blob/d4a44ded8c150aac89b37c1f665b5a749fe52b02/agents/planner.md
[ecc-multi]: https://github.com/affaan-m/ECC/blob/d4a44ded8c150aac89b37c1f665b5a749fe52b02/commands/multi-plan.md
[ecc-canvas]: https://github.com/affaan-m/ECC/blob/d4a44ded8c150aac89b37c1f665b5a749fe52b02/skills/plan-canvas/SKILL.md
[ecc-gan]: https://github.com/affaan-m/ECC/blob/d4a44ded8c150aac89b37c1f665b5a749fe52b02/agents/gan-planner.md
[ooo-ambiguity]: https://github.com/Q00/ouroboros/blob/188020bf1e406e0d276e8cfdd5f95f92e9fed7f5/src/ouroboros/bigbang/ambiguity.py
[ooo-pipeline]: https://github.com/Q00/ouroboros/blob/188020bf1e406e0d276e8cfdd5f95f92e9fed7f5/src/ouroboros/evaluation/pipeline.py
[ooo-independence]: https://github.com/Q00/ouroboros/blob/188020bf1e406e0d276e8cfdd5f95f92e9fed7f5/src/ouroboros/evaluation/reviewer_independence.py
[symposium-readme]: https://github.com/Q00/Symposium/blob/60037854824e369b004703de30877a6c88530f60/README.md
[symposium-harness]: https://github.com/Q00/Symposium/blob/60037854824e369b004703de30877a6c88530f60/skills/interview-harness/SKILL.md
[super-brainstorm]: https://github.com/obra/superpowers/blob/bb92a77741419a4ab5f06e711a283343f1ada0c3/skills/brainstorming/SKILL.md
[super-plans]: https://github.com/obra/superpowers/blob/bb92a77741419a4ab5f06e711a283343f1ada0c3/skills/writing-plans/SKILL.md
[omc-plan]: https://github.com/Yeachan-Heo/oh-my-claudecode/blob/454bae017356ed1d056182cd929b6eb6cf6143ad/skills/plan/SKILL.md
[omx-plan]: https://github.com/Yeachan-Heo/oh-my-codex/blob/2db7d5136b22252e83091a12ea27567b2fdd5971/skills/plan/SKILL.md
[omx-ralplan]: https://github.com/Yeachan-Heo/oh-my-codex/blob/2db7d5136b22252e83091a12ea27567b2fdd5971/skills/ralplan/SKILL.md
[ce-plan]: https://github.com/EveryInc/compound-engineering-plugin/blob/50532b00de523980010d97fe950965b35382a3b7/skills/ce-plan/SKILL.md
[ce-research]: https://github.com/EveryInc/compound-engineering-plugin/blob/50532b00de523980010d97fe950965b35382a3b7/skills/ce-plan/references/research.md
[ce-structure]: https://github.com/EveryInc/compound-engineering-plugin/blob/50532b00de523980010d97fe950965b35382a3b7/skills/ce-plan/references/structure.md
[ce-review]: https://github.com/EveryInc/compound-engineering-plugin/blob/50532b00de523980010d97fe950965b35382a3b7/skills/ce-plan/references/final-review.md
[ce-universal]: https://github.com/EveryInc/compound-engineering-plugin/blob/50532b00de523980010d97fe950965b35382a3b7/skills/ce-plan/references/universal-planning.md
[gstack-eng]: https://github.com/garrytan/gstack/blob/3b7254a54d3291c559b39b8ff7014b040d2650b0/plan-eng-review/SKILL.md
[gstack-sections]: https://github.com/garrytan/gstack/blob/3b7254a54d3291c559b39b8ff7014b040d2650b0/plan-eng-review/sections/review-sections.md
[gstack-auto]: https://github.com/garrytan/gstack/blob/3b7254a54d3291c559b39b8ff7014b040d2650b0/autoplan/SKILL.md
[pwf-skill]: https://github.com/OthmanAdi/planning-with-files/blob/7056ed2f2b86a8a9e18840f625ac66a48fa07693/.agents/skills/planning-with-files/SKILL.md
[pwf-complete]: https://github.com/OthmanAdi/planning-with-files/blob/7056ed2f2b86a8a9e18840f625ac66a48fa07693/.agents/skills/planning-with-files/scripts/check-complete.sh
[matt-grill]: https://github.com/mattpocock/skills/blob/49dd158d1076134a641b33efb035946536778336/skills/productivity/grill-me/SKILL.md
[matt-grilling]: https://github.com/mattpocock/skills/blob/49dd158d1076134a641b33efb035946536778336/skills/productivity/grilling/SKILL.md
[gsd-core-readme]: https://github.com/open-gsd/gsd-core/blob/b747aca5b1dcff699c36d90c5b9fca0ec6354c1c/README.md
[gsd-core-checker]: https://github.com/open-gsd/gsd-core/blob/b747aca5b1dcff699c36d90c5b9fca0ec6354c1c/agents/gsd-plan-checker.md
[gsd-checker]: https://github.com/gsd-build/get-shit-done/blob/bdcaab2c752d9a33a1a1ca9acf3a3c81fb991815/agents/gsd-plan-checker.md
[plannotator-readme]: https://github.com/backnotprop/plannotator/blob/34432f0aeb5456efe220529d0d263d301dbd0ea6/README.md
[plannotator-codex]: https://github.com/backnotprop/plannotator/blob/34432f0aeb5456efe220529d0d263d301dbd0ea6/apps/codex/README.md
[aider-modes]: https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/website/docs/usage/modes.md
[aider-code]: https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/coders/architect_coder.py
[council-readme]: https://github.com/karpathy/llm-council/blob/92e1fccb1bdcf1bab7221aa9ed90f9dc72529131/README.md
[council-code]: https://github.com/karpathy/llm-council/blob/92e1fccb1bdcf1bab7221aa9ed90f9dc72529131/backend/council.py
[odr-readme]: https://github.com/langchain-ai/open_deep_research/blob/1b7d2e80db9faa586165c60e09096dbbfd483a64/README.md
[odr-config]: https://github.com/langchain-ai/open_deep_research/blob/1b7d2e80db9faa586165c60e09096dbbfd483a64/src/open_deep_research/configuration.py
[gptr-readme]: https://github.com/assafelovic/gpt-researcher/blob/3582a6841fe7dc801e2a34e34ee408641aea9bce/README.md
[seq-readme]: https://github.com/modelcontextprotocol/servers/blob/bbb701e7ac1e57f3edd1c2836b94c5457eaf7b9c/src/sequentialthinking/README.md
[seq-code]: https://github.com/modelcontextprotocol/servers/blob/bbb701e7ac1e57f3edd1c2836b94c5457eaf7b9c/src/sequentialthinking/lib.ts

## Snapshot index

Repository state and default-branch commit at retrieval. Activity is descriptive, not a quality score. `Not archived` is not a maintenance guarantee.

| Repository | Commit | Commit date (UTC) | Repository state | Root license metadata |
|---|---|---|---|---|
| [Aider-AI/aider](https://github.com/Aider-AI/aider) | [5dc9490bb3](https://github.com/Aider-AI/aider/commit/5dc9490bb35f9729ef2c95d00a19ccd30c26339c) | 2026-05-22 | Not archived | Apache-2.0 |
| [EveryInc/compound-engineering-plugin](https://github.com/EveryInc/compound-engineering-plugin) | [50532b00de](https://github.com/EveryInc/compound-engineering-plugin/commit/50532b00de523980010d97fe950965b35382a3b7) | 2026-10-11 | Not archived | MIT |
| [OthmanAdi/planning-with-files](https://github.com/OthmanAdi/planning-with-files) | [7056ed2f2b](https://github.com/OthmanAdi/planning-with-files/commit/7056ed2f2b86a8a9e18840f625ac66a48fa07693) | 2026-10-10 | Not archived | MIT |
| [Q00/Symposium](https://github.com/Q00/Symposium) | [6003785482](https://github.com/Q00/Symposium/commit/60037854824e369b004703de30877a6c88530f60) | 2026-08-03 | Not archived | MIT |
| [Q00/ouroboros](https://github.com/Q00/ouroboros) | [188020bf1e](https://github.com/Q00/ouroboros/commit/188020bf1e406e0d276e8cfdd5f95f92e9fed7f5) | 2026-10-11 | Not archived | MIT |
| [Yeachan-Heo/oh-my-claudecode](https://github.com/Yeachan-Heo/oh-my-claudecode) | [454bae0173](https://github.com/Yeachan-Heo/oh-my-claudecode/commit/454bae017356ed1d056182cd929b6eb6cf6143ad) | 2026-10-06 | Not archived | MIT |
| [Yeachan-Heo/oh-my-codex](https://github.com/Yeachan-Heo/oh-my-codex) | [2db7d5136b](https://github.com/Yeachan-Heo/oh-my-codex/commit/2db7d5136b22252e83091a12ea27567b2fdd5971) | 2026-10-06 | Not archived | MIT |
| [affaan-m/ECC](https://github.com/affaan-m/ECC) | [d4a44ded8c](https://github.com/affaan-m/ECC/commit/d4a44ded8c150aac89b37c1f665b5a749fe52b02) | 2026-10-11 | Not archived | MIT |
| [assafelovic/gpt-researcher](https://github.com/assafelovic/gpt-researcher) | [3582a6841f](https://github.com/assafelovic/gpt-researcher/commit/3582a6841fe7dc801e2a34e34ee408641aea9bce) | 2026-10-10 | Not archived | Apache-2.0 |
| [backnotprop/plannotator](https://github.com/backnotprop/plannotator) | [34432f0aeb](https://github.com/backnotprop/plannotator/commit/34432f0aeb5456efe220529d0d263d301dbd0ea6) | 2026-10-11 | Not archived | Apache-2.0 |
| [garrytan/gstack](https://github.com/garrytan/gstack) | [3b7254a54d](https://github.com/garrytan/gstack/commit/3b7254a54d3291c559b39b8ff7014b040d2650b0) | 2026-10-11 | Not archived | MIT |
| [gsd-build/get-shit-done](https://github.com/gsd-build/get-shit-done) | [bdcaab2c75](https://github.com/gsd-build/get-shit-done/commit/bdcaab2c752d9a33a1a1ca9acf3a3c81fb991815) | 2026-05-31 | Archived | MIT |
| [karpathy/llm-council](https://github.com/karpathy/llm-council) | [92e1fccb1b](https://github.com/karpathy/llm-council/commit/92e1fccb1bdcf1bab7221aa9ed90f9dc72529131) | 2025-11-22 | Not archived | Not detected |
| [langchain-ai/open_deep_research](https://github.com/langchain-ai/open_deep_research) | [1b7d2e80db](https://github.com/langchain-ai/open_deep_research/commit/1b7d2e80db9faa586165c60e09096dbbfd483a64) | 2026-08-10 | Archived | MIT |
| [mattpocock/skills](https://github.com/mattpocock/skills) | [49dd158d10](https://github.com/mattpocock/skills/commit/49dd158d1076134a641b33efb035946536778336) | 2026-10-09 | Not archived | MIT |
| [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) | [bbb701e7ac](https://github.com/modelcontextprotocol/servers/commit/bbb701e7ac1e57f3edd1c2836b94c5457eaf7b9c) | 2026-10-11 | Not archived | Transition notice; see discussion above |
| [obra/superpowers](https://github.com/obra/superpowers) | [bb92a77741](https://github.com/obra/superpowers/commit/bb92a77741419a4ab5f06e711a283343f1ada0c3) | 2026-10-10 | Not archived | MIT |
| [open-gsd/gsd-core](https://github.com/open-gsd/gsd-core) | [b747aca5b1](https://github.com/open-gsd/gsd-core/commit/b747aca5b1dcff699c36d90c5b9fca0ec6354c1c) | 2026-10-11 | Not archived | MIT |

[ooo-gate]: https://github.com/Q00/ouroboros/blob/188020bf1e406e0d276e8cfdd5f95f92e9fed7f5/src/ouroboros/evaluation/models.py#L566
