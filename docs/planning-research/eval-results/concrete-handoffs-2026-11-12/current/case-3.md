# Investigate onboarding before choosing a feature

Use the two weeks to establish a defensible 30-day completion picture and distinguish three explanations: people cannot complete setup, they lose momentum despite understanding it, or the product differs from what they expected. The decision at the end is which explanation merits the next focused validation, or whether measurement gaps prevent that choice. Do not select reminders or another feature from the current evidence.

The analyst owns event coverage and cohort analysis. The product researcher owns consenting opt-in-panel interviews. Both synthesize the evidence. Existing de-identified data and the opt-in panel are the only research channels; no new tracking, unsolicited outreach or gamification is included. All starting facts come from [Case 3](../../../eval-fixtures/concrete-handoffs.md#case-3--product-investigation); nothing has been independently measured for this plan. Outcomes are pending.

## What the existing evidence establishes

| Supplied evidence | What it supports | What it does not establish |
|---|---|---|
| 100 starters last month; 40 completed within seven days | A supplied seven-day completion figure of 40% | The 30-day rate, why others had not completed, or whether event coverage is reliable |
| Six recent support messages mention confusing setup | Confusion is worth investigating | Six affected members of the 100-person cohort, prevalence, or causation; these messages may concern existing users |
| No interviews or controlled comparisons | A need for exploratory evidence | A justified feature choice or causal attribution |

Do not relabel the other 60 starters as 30-day failures. Some may complete later or may not yet have 30 days of follow-up. Support messages and interview accounts provide different evidence from the cohort and must not be merged into a single denominator.

## Two-week work plan

| When | Analyst | Product researcher | Finished result |
|---|---|---|---|
| Days 1–2 | Audit start/completion event definitions, identifiers, timestamp consistency, duplicates and missing/ambiguous stages. Determine which starters have a full 30-day observation window and which historical cohorts are usable. | Review the six messages for specific confusion patterns without assuming cohort membership. Recruit through the existing opt-in panel and prepare a neutral interview guide. | Written metric definitions, coverage limits and eligible cohort counts; an interview sample and guide covering all three hypotheses. |
| Days 3–6 | Calculate mature-cohort 30-day completion, with seven-day completion as a secondary view for the same cohort. Inspect observable steps, time to completion and return patterns. Flag unobservable transitions. | Aim for 6–8 consenting recent starters across completers, people who paused and people who report not completing after 30 days, as panel availability permits. Reconstruct their actual experience before probing the hypotheses. | A cohort table with denominators and observation windows; individual interview evidence with chronology, quotations or notes, contrary examples and recruitment limitations. |
| Days 7–8 | Check whether apparent drop-offs survive coverage and denominator checks; compare relevant patterns without making small subgroups appear precise. | Fill the most decision-relevant sample gap through the same panel if time permits; otherwise state the gap. Compare interviews with the observed patterns. | A hypothesis comparison that separates supporting, contrary and unavailable evidence. |
| Days 9–10 | Together, review the strongest competing explanation and whether the data could distinguish it. Produce a short decision brief and choose the next discriminating observation. | Together with the analyst. | A supported priority for further validation, or an explicit inconclusive result with the cheapest useful next check. |

The recruitment target is a practical two-week assumption, not a representative sample or a promise of saturation. If the panel cannot supply a category, finish the available work and report that limitation rather than expanding outreach.

## Make the primary metric trustworthy

Define completion using the existing product/event semantics, with the first qualifying onboarding start as the cohort anchor. Confirm whether restarts and duplicate events can be distinguished; do not invent a definition simply to make the counts line up. Report the count of eligible starters, completion count and rate, data cutoff, and relevant coverage limitations together.

The primary estimate uses people with at least 30 days of follow-up. Recent starters remain visible as immature observations, not failures. If last month's cohort is not fully mature, analyze its mature subset and a recent earlier, sufficiently observed cohort where available, labeling dates and any comparability limits. Show seven-day completion for the same mature cohort; retain the supplied 40/100 separately until its definitions and observation window are verified.

Missing completion events cannot automatically mean failure. If coverage cannot support a trustworthy rate, produce the audit and bounds only where their assumptions are defensible; state that the 30-day baseline remains unknown. The interview work can still proceed. No new tracking is part of this investigation; any later measurement change would be a separate proposal.

## Distinguish the explanations

| Hypothesis | Discriminating observations to seek | Evidence that would weaken it |
|---|---|---|
| Confusing setup | Accounts of a specific misunderstood step, what the participant tried, and whether the observable journey stalls at that step; ask completers how they resolved it. | Participants understand and traverse the steps, then stop for reasons unrelated to setup; apparent drop-off disappears after correcting coverage. |
| Loss of momentum; reminders might help | Participants describe understanding the next step and wanting the outcome but pausing because of competing demands or forgetting; existing events show pauses and later returns consistent with that account. | Participants deliberately decline to continue, cannot perform the next step, or return repeatedly without progressing. |
| Expectations mismatch | Compare what participants expected before starting with what they encountered and wanted to achieve; seek the point at which continuing no longer seemed worthwhile. | Participants report a clear fit and continued intent, with a concrete procedural barrier instead. |

Begin interviews with “Walk me through the last time you tried to get started,” then probe expectations, the point of stopping, attempted workarounds and later returns. Do not begin with “Would a reminder help?” Hypothetical enthusiasm for a feature is weak evidence of its effect. Use participants' accounts to interpret patterns, not to establish that a feature causes completion.

Interview participation and self-reported completion may be selective. Keep panel accounts separate from de-identified cohort results unless a linkage is already explicitly permitted; this plan does not authorize identifying analytics records. Agreement between unrelated support anecdotes and interviews is suggestive, not proof that they explain the cohort rate.

## What the final decision should be

Prefer this combined data audit and qualitative investigation over either an immediate reminder experiment or a data-only funnel exercise. The former would commit to one explanation before establishing the primary metric; the latter cannot reliably distinguish forgetting from confusion or mismatch. If event coverage is sound and one explanation has specific supporting accounts plus consistent journey evidence, prioritize a narrowly targeted validation of that explanation. Preserve plausible competing explanations and contradictory cases.

If evidence is mixed, choose the next observation that would separate the leading explanations; do not force a winner. If measurement is the decisive blocker, recommend the smallest separately authorized measurement repair and state which product conclusions remain unsupported. A controlled feature comparison can be a subsequent proposal, not an activity silently added to these two weeks.

The investigation is complete when it delivers: a usable 30-day baseline or a precise explanation of why one is unavailable; the secondary seven-day view with correct denominators; evidence for and against all three hypotheses; and a next-step recommendation whose strength matches that evidence. It is not complete merely because interviews were held, and it need not end with a feature decision. The next action is the day 1 event audit and opt-in-panel recruitment, which can proceed independently.
