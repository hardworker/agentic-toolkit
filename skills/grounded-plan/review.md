# Bounded review procedure

Read this for standard/deep planning or review of an existing plan. The parent owns the artifact; reviewers return findings rather than modifying it. Use fresh contexts with only the brief, constraints, acceptance criteria, evidence pointers, and the input specified below; do not reuse a research scout as the fresh critic of its own work. Tool access is read-only except a designated scratch output, if needed. Local instructions and the user's limits still apply.

## Standard

Dispatch one fresh critic against a fixed plan snapshot. Its task:

> Check this plan against the requested outcome and the supplied source artifacts. Open the relevant sources; do not judge only from the author's summary. Seek unsupported decision-changing claims, missed reuse, missing acceptance coverage, infeasible interfaces, dependency gaps, failure paths, and disagreement between diagrams and prose. Challenge unnecessary complexity with a concrete smaller alternative that preserves the goal. Distinguish existing behavior from proposed behavior and future checks from executed evidence. Report at most five material findings. No finding is required when the plan is sound. For each, give the affected claim/task, evidence pointer, consequence, and correction or observation that would resolve it. Label uncertainty honestly. Return a short verdict: ready, revise, or unresolved; this is advice, not implementation authorization.

The parent verifies material findings, corrects supported issues, and records any remaining unknown or user decision. If a correction changes a consequential part of the plan, one targeted follow-up may check that change. Otherwise stop. Do not add reviewers because the first found nothing.

## Deep

Use two fresh contexts, each with the same task, constraints, acceptance criteria, and evidence access:

1. **Critic:** the standard brief plus the fixed plan snapshot.
2. **Alternative author:** the brief below, **without the first plan, favored option, or critic's findings**.

> Independently recommend the smallest credible approach to this task. Inspect relevant source artifacts. Identify the strongest alternative, the decisive tradeoff, and what observation would change your choice. Surface at most five material assumptions or failure scenarios with evidence or an explicit unknown. A compact recommendation is enough; do not write a second full implementation plan. Do not ask the other reviewer or read their output before returning yours.

The parent should freeze its draft before receiving the alternative. First answers stay separate until both return. If only one context can run at a time, run them sequentially with the same information boundary. Reusing one reviewer to play both roles does not create a second initial judgment.

Compare the resulting choices and findings. Combine identical findings once; distinguish agreement reached independently from concessions during discussion. Challenge only disagreements that could alter the plan or leave a consequential acceptance criterion unsupported.

For each dispute, send each reviewer the relevant finding and opposing evidence; ask for one of:

- **Accept/correct:** identify the evidence or reasoning error that changes the position.
- **Defend:** supply a new source observation or corrected inference, with a concrete consequence.
- **Unresolved:** explain the missing observation or user-value choice; do not repeat the argument.

Allow at most two dispute rounds, at most one response per reviewer in each round: **six review calls total**, including the initial two. Stop earlier when settled or when a complete round adds no evidence or corrected inference. The parent adjudicates against sources; an unavailable observation remains unknown. It can accept a user's stated preference without pretending that preference settles an empirical claim.

Revise the plan once the material choices are resolved. Check altered dependencies, acceptance coverage, and diagram consistency; further independent review must fit the existing cap. Report remaining dissent when the cap or evidence limit prevents resolution. A cap limits work, not what may be reported.

## Review receipt

Record mode, actual fresh contexts/review calls, model diversity if known, material changes caused by review, unresolved findings, and stop reason (`settled`, `no-new-evidence`, `cap`, or `review-unavailable`). Preserve evidence pointers, not a transcript of private reasoning. Nothing in the receipt proves an unexecuted implementation works.
