# Keeping documentation current: comparison and pilot

Recommend a small pilot of in-repository checks supporting document owners' review, with manual review as the comparison. Existing CI, owners and Git history make this a bounded way to learn whether concrete signals improve review. It does not establish that checks can assess semantic correctness, and it does not justify adopting either agent approach yet.

Artifact ID: C2. Status: proposed plan, 2026-10-31. Outcomes: pending. This file is the canonical exercise artifact; no live planning-library record was created.

## All four approaches

The descriptions below are the supplied evidence available today. Cost and suitability judgments are inferences about the workflows, not measured performance.

| Approach | Ownership | Discoverability | Update cost | Uncertainty | Small-pilot suitability |
|---|---|---|---|---|---|
| **A. Manual review** | Existing document owners assess recent changes and remain responsible for edits. | A weekly change list gives owners an entry point. Finding the affected passage depends on their knowledge and attention. | Little new machinery; repeated inspection and editing consume owner time. Neither effort nor missed changes is measured. | Owners may overlook a change or misunderstand its documentation impact. Git history alone cannot establish correctness. | Strong baseline using available people and history. Easy to stop or narrow. |
| **B. In-repository checks** | Check maintainers own reliable signals; document owners interpret findings and approve corrections. | Link failures and public-interface changes can point to concrete review targets. Coverage is limited to what the checks observe. | Initial check setup and maintenance, then investigation of findings. Existing CI is available; net time savings are unknown. | Passing checks cannot certify semantic accuracy. Interface flags may not imply an actual documentation defect. | Recommended challenger to A: bounded scope, existing CI and inspectable findings. |
| **C. Retrieval assistant** | A reviewer owns truth judgments; an operator maintains retrieval and suggestion quality. | Local search can surface passages that owners might not recall. Whether it retrieves the right passages is untested. | Search exists, but query preparation, suggestion production and evidence verification add work of unknown size. | A retrieved passage may reflect an older decision that remains valid. Apparent age is not proof of obsolescence. | Credible later pilot for hard-to-find passages; first requires an evaluation set that distinguishes stale text from valid history. |
| **D. Agent-maintained drafts** | The agent proposes; the human reviewer owns acceptance and publication. Workflow owners maintain draft generation. | Concrete diffs make proposed changes easy to inspect, but can obscure omitted or unnecessary edits. | A branch and reviewer workflow exist. Draft production may save writing effort or increase verification burden; neither is measured. | Factual accuracy, coverage and reviewer burden are unevaluated. A fluent diff is not evidence of correctness. | Suitable only as a bounded draft-only experiment after defining a trustworthy review basis. Larger uncertainty than A or B today. |

All four retain human approval and prohibit automatic publication. A local-search capability does not establish that C or D can run without a new hosted service; that feasibility would need checking before either is piloted. No new hosted service is part of the recommendation.

## Pilot design

Choose one documentation area with an available owner and a bounded set of recent repository changes. Use the existing review workflow and CI. The owner remains accountable for semantic correctness; the checks supply evidence rather than deciding what to publish.

1. **Establish the manual baseline.** Give the owner the weekly change list and record which passages they identify as needing review, which corrections they consider justified, and the time spent. Include a small sample of unchanged documentation where practical to detect mistaken assumptions about what a change affects.
2. **Assess the incremental signal from B.** Apply link validation and public-interface flags to the same scope, then record additional confirmed defects, useful review prompts, misleading findings and extra review time. Because the owner sees B second, this measures incremental help in this exercise; it is not a controlled causal estimate of relative productivity.
3. **Decide whether to continue.** Review the actual corrections and burden with the owner. Retain B if its added findings justify maintaining and reviewing the checks within the team's available capacity. Retain A alone if B adds little or produces disproportionate noise. Record uncertain cases and reasons rather than counting every flag as a success.

The pilot is complete when every sampled finding has a disposition, the owner has assessed the resulting corrections, time and limitations are recorded, and a continuation decision is documented. No publication is needed to finish the pilot. Before starting, choose a fixed sample and time budget that fit the owner's existing availability; those are reversible scope choices, not an implementation specification.

## Alternatives kept available

- **A alone:** retained as the fallback and baseline. Prefer it when documentation changes are sparse or checks add little useful signal. Its unknown miss rate remains a limitation.
- **C:** deferred because local search alone does not resolve whether a passage is outdated. Revisit if the pilot finds that locating relevant documentation, rather than validating it, is the main bottleneck.
- **D:** deferred because an available branch workflow does not establish factual accuracy or acceptable review effort. Revisit if evidence shows drafting effort dominates and a bounded comparison can test both correctness and reviewer burden without automatic publication or a new hosted service.

The deciding tradeoff is the specificity of B's observable signals against its limited semantic coverage. Evidence that owner review is already cheap and sufficient would reverse the recommendation toward A alone. No clarification is needed to prepare this pilot; adoption beyond it depends on results.

Checks: one self-check of all five requested comparison dimensions, retained alternatives, constraints and pilot observability. No performance measurements, CI runs or independent review occurred. Detailed execution receipt: [receipt](receipt.md). Stop reason: review-unavailable; empirical superiority remains unknown.
