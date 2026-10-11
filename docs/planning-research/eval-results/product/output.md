Recommend a gated test of a lightweight, self-selected onboarding checklist before committing to personalization. Compare it with a clear universal checklist; build no rules service. With two weeks and one engineer, the result may be **“insufficient evidence; do not launch yet.”** Lean effort is explicitly requested, so this plan uses source checks and self-review.

The hypothesis is that matching checklist copy/order to a newcomer’s stated goal improves meaningful collaboration enough to justify the added selection step, without increasing support effort. This tests the complete experience, including selection friction; it cannot establish that the workshop personas are valid customer segments. Scope is new workspaces and checklist guidance. Automated profiling, a rules service, and a broad rollout are outside this experiment.

The supplied evidence supports these boundaries:

| Claim and status | Evidence and implication |
|---|---|
| **Observed in supplied notes:** six support-recruited interviewees reported confusion. | [Input, lines 11–12](../../eval-fixtures/product.md#L11). Selection bias prevents estimating prevalence; confusion may reflect problems beyond checklist relevance. |
| **Observed report; unknown measurement:** activation is shown as 31%. | [Lines 13–14](../../eval-fixtures/product.md#L13). Neither a trustworthy baseline nor a sample-size input without its definition and denominator. |
| **Observed:** personas originated in a workshop; onboarding currently has one checklist. | [Lines 15–17](../../eval-fixtures/product.md#L15). Goal-based variants are hypotheses, not validated segments. |
| **Observed constraint:** event instrumentation and copy changes fit; a rules service probably does not. | [Lines 18–21](../../eval-fixtures/product.md#L18). Selection UI, assignment, traffic, and support measurement remain **unknown**. |

No claim above is independently corroborated. **Inferred:** a small routing experiment could test value cheaply if those unknown capabilities already exist; the notes do not establish its feasibility.

| Approach | Deciding tradeoff |
|---|---|
| **Recommended, conditional:** shared copy improvements in both arms; treatment adds self-selected goal and corresponding copy/order. | Directly tests the incremental experience, but needs inexpensive selection and persistent assignment. Use the proposed personas only as provisional drafting inputs. |
| Universal checklist clarity test plus instrumentation. | Copy and instrumentation fit the stated window; a comparison still needs valid assignment. Addresses confusion, but cannot answer whether personalization adds value. Use if the routing gate fails. |
| Keep onboarding unchanged while repairing measurement. | Prefer this if even a valid comparison or support guardrail cannot be established. A rules service offers no justified advantage within this window. |

Proposed dependency sequence: **definitions and feasibility → validated measurement → randomized exposure → complete outcome window → decision**. The current universal checklist remains the fallback.

1. **Days 1–2: resolve definitions and feasibility.** Product owner decides D1–D3 below. Engineer checks existing assignment, selection, eligible traffic, and support attribution. Accept when a written experiment specification and effort estimate fit the remaining window. If routing cannot fit, choose the universal alternative; if measurement cannot fit, stop at measurement work.
2. **Days 2–4: prepare and validate the experiment.** Prefer workspace-level randomization to reduce collaboration spillover (**assumption**, confirm against the product’s collaboration boundaries). Allocate eligible new workspaces 50:50, keep assignment stable, and analyze all assigned workspaces, including selection abandonment. Shared tasks use shared wording. Accept when synthetic journeys verify eligibility, assignment persistence, exposure, deduplication, activation, and support attribution; document exclusions before enrollment.
3. **Days 5–7: enroll only if traffic supports the agreed sample.** Keep variants fixed and avoid other onboarding changes. Track missing events, allocation imbalance, selection abandonment, and severe support regressions. Pause and restore the universal checklist on broken assignment or material harm. Seven-day outcomes for the last cohort mature by day 14. Insufficient expected enrollment makes this a feasibility pilot, not a launch experiment.
4. **Day 14: evaluate and decide.** Report denominators, absolute differences and uncertainty for activation and support effort, plus abandonment. Do not select favorable personas after looking at results. Launch only a limited monitored rollout if pre-agreed criteria pass; otherwise retain the universal checklist and record whether evidence indicates harm, no worthwhile gain, or unresolved uncertainty.

Decisions needed before enrollment:

- **D1 — Activation:** recommend a seven-day milestone involving successful collaboration with another person, rather than checklist completion. Product owner must specify the actual event, eligible population, and whether seven days captures normal use; a longer window means no launch conclusion within two weeks.
- **D2 — Business thresholds:** choose the minimum worthwhile absolute activation lift and support acceptance rule. Recommend requiring the activation interval’s lower bound to exceed that lift. Measure support handling minutes per eligible workspace, with ticket rate as a secondary measure; ticket count alone may miss workload. Preserve the stated no-increase goal. Any positive harm allowance needs an explicit business decision; absence of statistically significant harm is insufficient.
- **D3 — Evidence budget:** after D1–D2, obtain a consistently defined baseline and eligible traffic estimate, then calculate required sample under a predeclared analysis method. Recommend a fixed-horizon comparison with 95% intervals and 80% power as starting choices, not an assertion of sufficiency. If the required sample or support measurement cannot fit, approve a feasibility pilot with no launch claim, or extend the experiment in a separate decision.

Verification receipt: read only the skill and supplied input; checked evidence provenance, counterarguments, scope, dependencies, acceptance coverage, and consistency of the proposed sequence. No implementation, live data checks, sample calculation, user contact, or independent review occurred. No diagram was rendered. Work stopped at a self-checked planning artifact because the missing definitions, traffic, and business thresholds require decisions or evidence unavailable in this exercise.
