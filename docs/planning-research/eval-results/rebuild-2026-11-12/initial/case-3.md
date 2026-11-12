# Two-week investigation into onboarding completion

Status: proposed investigation, using only the Case 3 facts in `../../../eval-fixtures/concrete-handoffs.md`. The decision at the end is which explanation merits the next focused validation, or which measurement gap must be resolved first. This investigation will not select or build a feature. Gamification is excluded.

## Question and current evidence

What proportion of people who start onboarding complete within 30 days, where do incomplete journeys diverge, and which evidence best supports confusing setup, unmet expectations, or an interruption that a reminder might address? Completion within seven days is a secondary timing view, not a substitute for the primary question.

The packet reports 100 starters last month and 40 completions within seven days. It establishes neither a 30-day baseline nor the correctness and coverage of the event definitions. The six setup-related support messages are a useful source of questions, but they cannot be linked to that cohort and may concern existing users. They do not establish that six of the 100 starters experienced confusion, that confusion caused noncompletion, or how common it is.

Use two complementary methods: a reproducible analysis of existing de-identified events and interviews with consenting members of the existing opt-in panel. Event sequences can locate timing and friction; interviews can explain intentions and experiences. Neither alone, nor their combination without a controlled comparison, will establish a causal uplift from reminders or another feature.

## Define the measurement before interpreting the funnel

The analyst owns a short measurement specification and executable analysis using the available data. On days 1–2, inventory the existing events and fields, identify the actual start and completion signals, and examine de-identified sequences. Use the existing person identifier only if it reliably connects starts and completions; do not add tracking or construct a new identity linkage. Record missing identifiers, duplicate events, ordering anomalies, time-zone handling and any known logging/coverage boundary.

The proposed cohort rule is one person per first qualifying onboarding start in the defined calendar month. Repeated start events are one journey unless the existing event semantics establish a genuinely new onboarding process; document any resulting exclusion. Define completion as the product's existing terminal onboarding event or equivalent verified event sequence. If the available events do not establish a terminal outcome, report completion as unmeasurable from this extract rather than substituting an arbitrary activity event.

Freeze an extraction date and calculate elapsed time from each qualifying start:

| View | Denominator and numerator |
|---|---|
| Primary 30-day completion | Starters whose full 30-day observation window has elapsed and whose relevant events have adequate coverage; numerator is those completing within 30 elapsed days. |
| Secondary seven-day completion | The corresponding fully observed seven-day cohort and completions within seven elapsed days. |
| Timing comparison | For the same fully observed 30-day cohort, show completion by day 7 and by day 30 so different denominators do not masquerade as a timing effect. |
| Not yet observable or unreliable | Separately report immature windows, missing identity/coverage and exclusions. Never count them as confirmed noncompleters. |

If all 100 starters have mature, adequately covered windows, use that full cohort. If only some do, report the mature subset explicitly and refresh once near the end of week 2 if available data make more windows observable. Do not claim a full-month 30-day rate from a partial cohort. If coverage is systematically missing, a clean-subset rate may be biased; show the exclusion pattern and qualify or withhold the overall estimate.

Report counts alongside rates, a 95% binomial interval for the measured completion proportion, and completion timing. The interval expresses sampling variation, not correction for missing events or selection bias. With 100 starters, avoid a large segmentation exercise. Inspect the overall funnel and at most two preselected, reliably recorded dimensions that plausibly distinguish the hypotheses; select and record them after the coverage inventory, before comparing completion rates. If no suitable dimensions exist, use the overall journey only.

At each recorded setup step, show how many people reach it, how many reach the next step, and time between them. “Last recorded step” is an observation, not proof of abandonment at that screen. Compare completed and incomplete observed journeys descriptively; a difficult step can correlate with noncompletion without causing it. Reproduce the reported 40/100 seven-day figure where definitions allow and explain discrepancies instead of forcing agreement.

## Interview for competing explanations

The researcher recruits only through the existing consenting opt-in panel. Aim for eight interviews within the two weeks: five people reporting an incomplete recent onboarding journey and three reporting completion, prioritizing recent journeys with a full 30-day window. This is a purposive contrast, not a representative survey or a statistically powered sample. If fewer eligible people are available, interview those available and report the gap; do not use unsolicited outreach to fill quotas.

Use self-reported journey status for interview sampling. Do not assume panel members can be linked to the de-identified event cohort, or that consent for interviews permits such linkage. Record interview dates and approximate onboarding timing so recall limitations and immature journeys remain visible.

Use 40–45 minute sessions with a common guide:

1. Ask what brought the participant to the product and what result they expected, before mentioning hypotheses.
2. Reconstruct their actual onboarding attempt: what they tried, where they paused, what they understood, and what happened afterward.
3. Ask about return attempts, outside interruptions, unmet prerequisites and whether the expected benefit still seemed worthwhile.
4. When the participant is willing and the existing flow is accessible, observe them explaining or navigating the relevant setup step without coaching. Use the existing experience, not a reminder or redesign prototype. Stop short of requiring a consequential account change.
5. Ask what helped completion or what would have made progress possible. Only at the end probe missing explanations with neutral questions. Do not treat “I would like a reminder” as evidence that a reminder would improve completion.

Keep consented research notes with participant pseudonyms and minimal necessary detail, using the existing panel's handling rules. No new product tracking is introduced. Distinguish recalled events, directly observed confusion and hypothetical preferences in the notes. The supplied support messages can inform neutral probes but are a separate evidence set.

## Analyze without preselecting a solution

The analyst and researcher maintain a shared hypothesis matrix. Code each interview against all three explanations, allow multiple explanations per person, and retain contradictory and unexplained cases. Count participants, not repeated quotations, when describing how often a theme appeared. Both roles review a few of the same notes to catch different interpretations, then resolve the coding terms before synthesis.

| Explanation | Evidence that strengthens it | Evidence that weakens it or leaves it unresolved | Decision the evidence could support |
|---|---|---|
| Setup is confusing or hard to complete | Repeated difficulty at a concrete step, inability to explain what to do, observed misunderstanding; compatible event concentration or repeats. | Participants understand and complete the step; pauses occur elsewhere; missing events could mimic the funnel pattern. | Validate the specific setup problem and a focused correction in a later study. |
| Expectations do not match the product | Participants describe an expected benefit the product does not provide or decide the value is insufficient after learning what it does. | Expected benefit remains clear and desired; interruption or a practical prerequisite better explains the pause. | Investigate the expectation-setting moment or product-fit question before choosing an intervention. |
| People intend to finish but lose the opportunity or forget | Clear continuing intent, understood next step, feasible prerequisites, interruption/forgetting accounts, and compatible return timing. | People are blocked, confused, uninterested, or explicitly choose not to continue. A positive reaction to a reminder idea alone is insufficient. | Consider a later consented controlled comparison of reminders, with its own authorization and design. |

No single metric ranks these explanations causally. Stronger evidence means a specific repeated mechanism with a clear path to completion, corroboration where available and no unresolved contradiction that undermines it. Panel selection and recall bias limit generalization. The six support messages may corroborate wording or a step, but never become a cohort prevalence estimate.

On day 10, use this decision rule:

- If the primary outcome cannot be measured reliably, deliver the measurement failure and the smallest repair or further audit needed. Interviews can still nominate candidate problems, but no claim of onboarding uplift follows.
- If one concrete mechanism recurs across multiple independent interviews and is compatible with reliable event evidence, recommend the next focused validation of that mechanism. If two explanations remain plausible, recommend the observation or comparison that would distinguish them.
- If evidence is sparse, conflicting or selected in ways that prevent a defensible direction, report an inconclusive result and the next bounded evidence need. Do not break the tie by choosing reminders.

## Two-week work and outputs

| When | Analyst | Researcher | Observable result |
|---|---|---|---|
| Days 1–2 | Audit coverage; define cohort and outcomes; identify mature windows. | Confirm panel eligibility and consent; recruit; prepare neutral guide. | Measurement specification with known limitations; interview schedule or recruitment shortfall. A coverage problem changes the analysis claims immediately. |
| Days 3–5 | Produce initial counts, timing and step progression; inspect anomalies. | Conduct first four interviews and code notes. | Reproducible initial analysis and evidence matrix containing all three hypotheses, including contrary cases. |
| Days 6–8 | Resolve data anomalies; complete the limited planned comparisons; refresh only if useful. | Conduct remaining interviews, using targeted neutral probes for unresolved distinctions. | Final analysis tables, interview summaries and documented gaps; no expanding research program. |
| Days 9–10 | Jointly reconcile measurement and qualitative findings. | Jointly compare explanations and draft the recommendation. | Decision memo with 30-day answer or explicit inability to answer, seven-day comparison, limitations, and one next investigation commitment. |

The final handoff includes the cohort/event specification, reproducible query or notebook, counts and funnel/timing tables, de-identified interview synthesis, hypothesis matrix and decision memo. It must make measured results, participant reports and interpretations distinguishable. Completion is delivery of a defensible next-evidence decision, including an inconclusive one, within the two weeks; it is not a feature launch or a promised increase in onboarding completion.

The immediate next step is the event-coverage audit and panel recruitment in parallel. The work is concrete enough to begin under the supplied access constraints. Actual event coverage, mature-cohort size and consenting participant availability remain unverified dependencies; each has the bounded fallback above.
