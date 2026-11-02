# Planning 0.9.0: refinement and compaction

**31 October 2026.** Implemented the authorized idea-shaping changes and shortened all four instruction files. The helper, invocation, storage format and installed symlink targets are unchanged. Readability and cost benefits remain unmeasured.

**2 November follow-up:** version 0.9.1 merges the scout and review text into `SKILL.md`, retaining `records.md` separately. The counts and results below describe 0.9.0; its original source hashes and outputs are preserved. This file reorganization was checked for text preservation and links, without rerunning the output trial.

## What changed

The main skill now challenges consequential proposed mechanisms before elaborating them, justifies scope without dropping requested breadth, defines acceptance as outcomes, preserves decisions and corrections, and stops intake on material clarity. Output guidance makes each substantial idea separately scannable while retaining rationale, architecture and flexible depth. Existing instructions were consolidated rather than moved into new files.

| Instruction file | Before | After |
|---|---:|---:|
| `SKILL.md` | 1,909 | 1,095 |
| `records.md` | 1,753 | 971 |
| `review.md` | 802 | 531 |
| `scouts.md` | 478 | 287 |
| **Total words** | **4,942** | **2,884** |

Whitespace-delimited counts include frontmatter: about **42% fewer instruction words** overall. This measures prompt size, not reader comprehension, model cost or output quality.

## What ran and what it changed

Three fresh contexts each applied one frozen skill snapshot to the same [four synthetic requests](eval-fixtures/planning-refinement.md): baseline, initial candidate and revised candidate. No answer or grading rubric was supplied. Each context handled all four cases once, with source facts supplied and external retrieval, nested agents, implementation and live-library access prohibited. Settings were inherited; no different-model comparison was established.

The initial candidate preserved the main obligations but produced long paragraphs covering multiple topics. Its output-grouping instruction was replaced with a more concrete direction: named sections or distinct items for substantial parts, with purpose, decisive details and essential conditions together. The same cases were rerun in a fresh context. The final larger outputs use named sections and separate responsibilities, comparisons or decisions. This is an observed structural change, not measured improvement in reader understanding.

A separate instruction critic found two lost safeguards: explicit `--new-session` precedence and dated outcome entries. Both were restored. One targeted follow-up checked those corrections and the revised grouping instruction, finding no remaining material issue. That verdict addresses instruction preservation, not empirical benefit.

## Output inspection

The parent inspected the actual outputs against the requests. The baseline was already capable on these cases; no broad quality superiority is established.

| Case | Observation | Inspect the pair |
|---|---|---|
| Overbuilt support service | Both retain weekly reporting, CSV, local evidence, human approval and the dashboard exclusion. Both defer unsupported infrastructure and retain architecture plus a first proof. The final candidate separates responsibilities into assessable items. | [Baseline](eval-results/refinement-2026-10-31/baseline/case-1.md), [final](eval-results/refinement-2026-10-31/final-candidate/case-1.md) |
| Broad documentation survey | All four approaches and all five requested dimensions survive alongside a pilot. Alternatives and the publication/hosting limits remain visible. | [Baseline](eval-results/refinement-2026-10-31/baseline/case-2.md), [final](eval-results/refinement-2026-10-31/final-candidate/case-2.md) |
| Already-clear plan | Both preserve the supplied plan verbatim and request no new interview or implementation scope. The final review response is slightly longer; shorter is not the success criterion. | [Baseline](eval-results/refinement-2026-10-31/baseline/case-3.md), [final](eval-results/refinement-2026-10-31/final-candidate/case-3.md) |
| Early research | Both retain the corrected 30-day question, secondary 7-day view, competing explanations and excluded gamification. Neither turns reminders into a commitment or invents a delivery roadmap. Cohort and consent limits remain explicit. | [Baseline](eval-results/refinement-2026-10-31/baseline/case-4.md), [final](eval-results/refinement-2026-10-31/final-candidate/case-4.md) |

The [initial candidate](eval-results/refinement-2026-10-31/initial-candidate/receipt.md) and all outputs remain available. The [manifest](eval-results/refinement-2026-10-31/manifest.json) records source/output hashes and word counts; [the patch](eval-results/refinement-2026-10-31/initial-to-final.patch) reconstructs the initial candidate by reversing it against the instructions at `final_candidate_git_ref` (`ccc2d35`), not the current skill. Only paths were normalized in saved outputs. Baseline sources are available at the manifest's Git revision.

## Verification and limits

- **Compatibility:** 14 existing session/discovery tests passed. `sessions.py`, the license and invocation arguments are unchanged. Existing Codex and Claude symlinks resolve to this checkout. These checks do not exercise fresh host invocation or prove model adherence to the revised prose.
- **Document checks:** YAML/frontmatter, plugin metadata, local links/anchors, fences, public-path hygiene and whitespace were checked. The bundled validator could not run because PyYAML is absent; Ruby parsed the frontmatter instead. A stale records-to-output anchor was corrected.
- **Work performed:** three artifact-generation contexts; one instruction critic plus one targeted follow-up. Each generation context performed its own artifact checks. Actual token/billing totals were unavailable.
- **Coverage limits:** one run per snapshot, four cases within each context, synthetic supplied facts, and author assessment without blind grading. Conversation corrections were supplied together, not exercised as live cross-turn persistence. Source access restrictions were instructions, not a per-agent security sandbox. Mermaid diagrams were inspected but not rendered. No real product, full Ouroboros runtime, live research or user-comprehension study ran.

Stop reason: the bounded comparison and instruction review are complete. The user authorized implementation; adopting these instructions does not establish general planning benefit. The next useful evidence is feedback on real plans, particularly missed decisions, unnecessary work and effort needed to understand each section.
