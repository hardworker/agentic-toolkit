# Onboarding completion: next research direction

Investigate why people do or do not complete onboarding within **30 days**, prioritizing confusing setup and a mismatch between expectations and the product. Keep completion within seven days as a secondary timing view. The research should decide which explanation deserves a subsequent targeted test, or whether the evidence supports no feature intervention yet.

Artifact ID: C4. Status: proposed research direction, 2026-10-31. Outcomes: pending. This file is the canonical exercise artifact; no live planning-library record was created.

## What the evidence supports today

The supplied cohort has 100 onboarding starters and 40 completions within seven days: a 40% seven-day completion rate. Thirty-day completion is unknown. People who have not completed at day seven cannot be treated as permanent losses, and anyone without 30 days of follow-up cannot yet be classified as a 30-day non-completer.

The six support messages make setup confusion worth investigating. They do not estimate its prevalence or explain the cohort's non-completion: the messages are unlinked to those 100 people and may include existing users. There are no interviews or controlled comparisons. These are supplied facts, not newly inspected data.

The later update replaces seven-day completion as the main question and explicitly adds expectation mismatch. Reminders remain a hypothesis, not a selected solution. Gamification stays excluded.

## Competing explanations and discriminating evidence

| Explanation | Next observation | Evidence that would weaken it |
|---|---|---|
| **Confusing setup** | Look for concentration of stalls or repeated attempts at specific existing setup events. Ask consenting participants to describe where they became unsure and what they expected to do next. | Non-completers understood the steps and report stopping for unrelated reasons; event patterns show no consistent difficulty. Absence of detailed events alone would not disprove confusion. |
| **Expectation–product mismatch** | Compare what participants expected before starting with what they discovered during onboarding, including whether the eventual product seemed useful to them. | Participants still wanted the offered outcome and describe a concrete obstacle to reaching it rather than a mismatch. |
| **Timing, interruption or forgetting** | Compare seven-day and 30-day completion and observed return patterns. Ask whether people intended to return and what interrupted them. | People explicitly chose not to continue, or returned repeatedly but remained blocked. This would make a reminder-first explanation less plausible. |
| **Technical or access barriers** | Use existing events to identify failures where visible, and ask about errors or unavailable prerequisites. | Participants could proceed technically and consistently describe another reason for stopping. Missing error instrumentation remains uncertainty. |
| **Measurement or cohort-definition problems** | Verify what the existing completion event means, whether event sequences are plausible, and whether eligible starters have sufficient follow-up. | Consistent definitions and complete observation make measurement error less likely as the main explanation, without proving any behavioral cause. |

These explanations may coexist. Interviews can reveal mechanisms, while event data can describe patterns; neither alone establishes the causal effect of a proposed feature.

## Next evidence, in priority order

**First, establish a usable 30-day view.** The analyst should inspect existing de-identified data, preserving the current onboarding-start and completion definitions initially and documenting any ambiguity. Identify the number of starters with a full 30-day observation window, their completion count and timing, and those still awaiting sufficient follow-up. Retain the seven-day view for the same eligible cohort so timing comparisons have a clear denominator. If the available cohort is immature, report the limitation and wait for observation to mature rather than inventing a 30-day rate.

**Then, locate contrasts worth explaining.** Using only existing events, compare early completers, later completers and mature non-completers. Look for common stopping points, return attempts and failures where recorded. Treat small subgroup differences as exploratory. This narrows interview questions without presuming that a particular event pattern proves confusion or mismatch.

**Pair those contrasts with consenting participants' accounts.** The researcher should use an already authorized consent route and seek accounts from completers and non-completers where possible. Begin with participants' goals and experience; probe setup understanding, expected value, obstacles and reasons for returning or leaving. Avoid leading with reminders. Keep the six support messages as a separate source of questions unless a legitimate link to the cohort becomes available; do not assume they corroborate event patterns.

No new tracking or unsolicited outreach is authorized. If the needed detail is absent, name the evidence gap rather than filling it with inferred behavior.

## Decision this research should support

Synthesize the mature-cohort timing, event patterns and participant accounts into a short explanation assessment: support, contradictory evidence, remaining uncertainty and the next observation that could change the conclusion. If an explanation becomes credible, propose a separately scoped test aimed at it. If evidence is mixed, preserve competing explanations and gather the missing evidence. Reminders warrant consideration only if interruption or forgetting among people who still want to finish is supported; an association alone would not establish that reminders improve completion.

The research is ready for that decision when 30-day eligibility is explicit, the strongest available evidence for and against the leading explanations is recorded, and missing evidence is distinguished from a negative finding. It need not end with a feature recommendation or a delivery roadmap.

**D1 — Interview access, if no authorized consent route exists.** Options are an existing consented participant pool, an event-only first pass, or separately requested outreach authorization. Prefer the existing pool when available; otherwise continue the event-only work. This condition blocks interviews only. No clarification is needed to begin the authorized evidence inspection or to use this research direction.

Checks: one self-check against the revised outcome window, both requested explanations, excluded gamification and authorization limits. No event analysis, interviews or controlled comparisons were executed. Independent review was prohibited. Detailed execution receipt: [receipt](receipt.md). Stop reason: review-unavailable; the next missing observations are specified.
