# Investigating onboarding completion

Spend the two weeks establishing a trustworthy 30-day completion baseline and distinguishing three explanations: people forget to return, setup is confusing, or the product differs from what they expected. The decision at the end is which uncertainty merits the next validation—or whether the evidence is still too weak to prioritize one. It is not a feature decision. Gamification is excluded.

Use the analyst's existing de-identified events and the researcher's consenting opt-in panel. No new tracking, unsolicited outreach or implementation is needed. Outcomes are pending.

## What the current evidence establishes

The source packet reports 100 starts and 40 completions within seven days last month: a 40% seven-day rate under its existing definitions. It supplies neither a 30-day rate nor verified event coverage. Do not treat the other 60 as 30-day non-completers.

Six support messages mention confusing setup. They make setup a useful interview topic, but cannot establish prevalence or explain the cohort because the senders cannot be linked to it and may be existing users. There are no interviews or controlled comparisons. None of the three explanations has causal support yet.

## Week one: validate measurement and seek contrasting accounts

**Analyst, days 1–2: define an interpretable cohort.** Record the extraction cutoff, time zone, start/completion definitions, deduplication rule and available identity continuity. Check which events and timestamps exist, missing or repeated transitions, and any known platform or release coverage differences using available event metadata. Verify that the completion event represents the intended onboarding endpoint; if existing data cannot establish that, label the metric unvalidated.

Include in the primary denominator only starts with a full 30-day observation window before the cutoff. Report the eligible count explicitly; last month's 100 may not all qualify. Count completion within 30 elapsed days of start, using the same population for the secondary seven-day view. Keep recent starts separately as incomplete follow-up, not failures. Show elapsed time to completion and stage counts where event coverage supports them. If too few people have a full window, use an earlier comparable cohort if available and disclose its dates and differences. Do not silently substitute the seven-day rate for the primary question.

The deliverable is a short measurement audit and reproducible cohort query, including missing coverage and how it affects interpretation. Event coverage is the first dependency: an invalid endpoint blocks quantitative conclusions, but does not block exploratory interviews.

**Researcher, days 1–2: recruit contrasts through the existing panel.** Seek six to eight consenting participants who recently began onboarding, including completers and people who stopped, with different apparent stopping points when panel information allows it. Ask about completion timing so late completers are not classified as failures. Participation and screen sharing remain voluntary. Do not attempt to re-identify the de-identified cohort or join panel participants to it without an existing authorized mechanism.

Panel availability and recollection are assumptions to test, not promised sample coverage. Record invitations through the permitted opt-in workflow, response counts and missing groups. A panel containing only successful users cannot represent people who abandoned onboarding; disclose that limitation and proceed with the accounts it can provide.

**Days 3–5: run the first interviews and describe the funnel.** The analyst reports exact counts for the eligible cohort, 30-day and seven-day completion, delays, and where users stop or return. Use only existing, sufficiently covered attributes for a few relevant contrasts; present small group counts without ranking them as reliable effects.

The researcher conducts initial interviews, starting with a neutral account of what the person expected, tried, encountered and did next. Ask for concrete episodes before introducing reminder or setup hypotheses. Where participants consent, have them explain a familiar step or show what confused them; do not create a new tracked experiment. Ask what made them return or stop, what other demands intervened and whether they still wanted the outcome. Record a consistent evidence summary with consent, participant category, observed behavior versus recalled explanation, supporting details and contradictions.

At the end of day 5, compare the sources. Use gaps and contradictory cases to target the remaining interviews, rather than rewriting the investigation around the most memorable account.

## Week two: challenge explanations and make the next decision

Complete the remaining interviews on days 6–8 and finish descriptive analyses in parallel. On days 9–10, the analyst and researcher reconcile the findings into one decision brief. Keep cohort measurements, panel accounts and the unlinked support messages separate; they are not three independent estimates of the same prevalence.

| Explanation | Evidence that would strengthen it | Evidence that would weaken it | Decision the evidence can support |
|---|---|---|---|
| Forgetting or competing demands | Participants understood the next step and still wanted the outcome, but stopped for outside reasons; return patterns are compatible with delayed attention | Accounts show unresolved setup difficulty or little interest after understanding the product | Prioritize a future, separately authorized test of whether a timely reminder helps; interviews alone cannot establish reminder effectiveness |
| Confusing setup | Concrete misunderstandings recur across contrasting participants, and a covered funnel stage shows compatible losses or retries | Participants explain and navigate setup successfully but stop for unrelated reasons | Prioritize a focused comprehension/usability validation of the implicated step, without committing to a feature |
| Expectations differ from the product | Participants describe a specific expected benefit and a different experienced one; stopping follows recognition of that difference | Expectations match the product and people still want to finish, but face another obstacle | Prioritize validation of the promise, audience or product understanding that appears mismatched |

Event gaps and delayed completion are competing explanations for the apparent problem itself. If 30-day completion differs substantially from the seven-day picture, distinguish delayed onboarding from abandonment before prioritizing an intervention. Without a stated acceptable completion target or comparison group, report the baseline rather than declaring an observed rate acceptable or unacceptable.

## Decision rules and completion

The final brief should contain the reproducible measurement definition and counts, a coverage assessment, a hypothesis table with supporting and contrary evidence, and one recommended next investigation with its decision criterion. Multiple causes may coexist. Prefer the explanation with the strongest concrete accounts and compatible reliable event evidence; do not turn the six support messages or panel proportions into cohort-wide estimates. If sources conflict, recommend the observation that would resolve the conflict instead of forcing a winner.

Complete the investigation when both people have delivered those artifacts and each hypothesis has either been assessed or explicitly marked unassessable with a reason. A useful outcome may be that measurement repair or broader consenting recruitment is needed before intervention research. Document any such follow-up as a proposal; new tracking and outreach beyond the existing panel require separate authorization.

The smallest credible approach combines existing-data analysis and contrasting interviews. Analysis alone can locate delay but not reliably explain it; interviews alone cannot establish cohort completion or prevalence. A controlled reminder comparison would answer an eventual treatment question more directly, but would prematurely select one mechanism and exceed the authorized investigation. Revisit it only if this work supports that hypothesis and an experiment is separately agreed.

There is no blocker to starting the audit and recruitment. A trustworthy quantitative conclusion depends on event validity and enough fully observed starts; representative qualitative coverage depends on who is available and consents. These are bounded investigation questions. No event analysis or interviews have been executed for this plan.
