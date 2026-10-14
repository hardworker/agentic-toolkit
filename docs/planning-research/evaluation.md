# Grounded Plan 0.1.0: pilot evaluation

Evaluation date: **12 October 2026** (some run timestamps are 11 October UTC). Candidate: [SKILL.md](../../skills/grounded-plan/SKILL.md) and [review procedure](../../skills/grounded-plan/review.md). Sources and fixture hashes accompany the [saved results](eval-results/manifest.json).

This report evaluates **0.1.0**, saved in commit `6397676`; the skill links above now open the current version. The original manifest hashes remain historical evidence. The subsequent user-wide storage and outcome extension is documented separately in [research decisions and outcomes](outcomes.md).

**The candidate demonstrated the intended basic behaviors on three synthetic tasks. It has not demonstrated superior planning quality or lower cost.** Native planning was already strong on the engineering case. The additional reviewers found no material defects in that completed plan, so this pilot supplies no observed quality gain from deeper review.

## What ran

Fresh contexts received only their task, permitted source files, and the skill where applicable. No upstream planning framework was executed. All agents inherited the host model settings; no cross-provider comparison was made. Exact model identifiers and token/billing telemetry were not available in the run receipts.

| Run | Observed result | Additional review work | Output |
|---|---|---|---|
| Native engineering plan | Found reuse, incomplete durability/concurrency, CSV escaping, retention and authorization gaps; separated future acceptance from the three passing existing tests | None | [Plan](eval-results/engineering-baseline/output.md), [receipt](eval-results/engineering-baseline/receipt.json) |
| Candidate engineering, standard | Covered the same major risks; added source pointers/evidence labels, decision IDs, a failing CSV probe, explicit rollout guardrails and rollback | One fresh same-model critic; zero follow-ups; no material findings | [Plan](eval-results/engineering-candidate/output.md), [receipt](eval-results/engineering-candidate/receipt.json) |
| Candidate product, lean | Challenged selection bias, undefined activation and unvalidated personas; made launch conditional on measurement and feasibility, with smaller fallbacks | No review agents | [Plan](eval-results/product/output.md), [receipt](eval-results/product/receipt.json) |
| Candidate research, review-only standard | Caught dependent sources, confounding, mismatched outcome/window, undefined effect and diagram order; recomputed descriptive arithmetic; preserved input | Fresh review prohibited; correctly reported self-check only | [Review](eval-results/research/output.md), [receipt](eval-results/research/receipt.json) |
| Deep review component on frozen engineering candidate | Critic independently reran tests/probe; blind alternative independently recommended reuse with measurement-triggered separation | Two fresh initial contexts; no material dispute, so zero dispute rounds | [Critic](eval-results/engineering-deep/critic.md), [alternative](eval-results/engineering-deep/alternative.md), [parent receipt](eval-results/engineering-deep/receipt.json) |

The deep test reused the standard candidate as its frozen plan. Its two calls are **additional evaluation work**, not part of the standard run's cost and not a full deep planning benchmark. The initial answers remained separate. Both favored the existing worker path, which is agreement about a small fixture, not independent empirical proof of a production design.

The fixture sources remained unchanged. Existing tests establish only sequential repeated-request behavior, tenant-scoped lookup, and simple output. The CSV probe demonstrates a defect in the deliberately limited fixture. None of these runs establishes production throughput, concurrency, end-to-end authorization, crash recovery, or seven-day download behavior.

## What this says about cost

| Mode | Policy ceiling | Pilot observation |
|---|---|---|
| Lean | No review calls | Product used none; useful caveats still required substantial author work. |
| Standard | One critic plus at most one targeted follow-up | Engineering used one critic; no material change followed. |
| Deep | Two initial reviewers plus at most two dispute rounds; six review calls maximum | Component test stopped after two initial calls; the escalation/cap branch was not exercised. |

These are work proxies. Research, context size, tool use, human decisions, and model choice can dominate the bill; a two-call run need not cost twice a one-call run. The baseline and standard engineering receipts record approximately 87 and 191 seconds respectively, but the clocks excluded different initial work and execution overlapped other runs. They are not a controlled latency comparison or a basis for dollar estimates.

The practical default remains a trial policy: lean for clear reversible work, one critic for substantive choices, and deep only for consequential uncertainty or an explicit request. The pilot supports resisting automatic extra rounds; it does not establish an optimal threshold or that standard review is cost-effective for every nontrivial task.

## Packaging and static checks

- Parsed the full frontmatter and checked required field types, name/folder agreement, scoped license, and local skill links. The repository requires `argument-hint`; the bundled Codex validator's whitelist rejects that extension. A temporary projection omitting only that field passed the bundled validator. This is **not** a claim that the complete manifest passed that validator or that every host accepts the extension.
- Checked plugin version, documentation links, whitespace, public-file hygiene, recorded hashes, and unchanged evaluation inputs. The skill's support files are flat beside `SKILL.md`, per repository convention.
- Diagram edges and prose were reviewed for agreement. Mermaid rendering was not tested. The product output chose tables and a text dependency sequence; a strict always-rendered-diagram requirement would require a stronger output rule and further testing.
- The candidate is an original three-file skill with a scoped MIT license. No upstream runtime, provider, or copied implementation is required. This pilot did not test marketplace publication or live skill discovery in every supported host.
- Created the repository-convention local links under `~/.agents/skills/` and `~/.claude/skills/` and verified that their skill contents match this checkout. These links depend on the checkout remaining available; this is an installation check, not a fresh-session invocation test.

## Limits and next useful checks

The author of the skill also assessed these outputs. Grading was not blind, there was one run per task/mode, the tasks were synthetic, and the same model family generated and reviewed them. Source/tool access was controlled by instructions rather than a per-agent filesystem sandbox. Receipts report that reviewers followed the restrictions; the experiment does not establish isolation against a malicious reviewer.

Not exercised: a destructive migration plan, a live web research task, ambiguous skill triggering, a genuine unresolved dispute reaching the round cap, cross-model disagreement, changing evidence mid-review, a host with hard billing limits, or durable continuation across sessions. These are explicit coverage gaps, not passing checks.

The next comparison should use repeated real tasks against native planning and `ce-plan`, with blind grading and actual token/tool usage when available. ECC-style inline planning is another useful low-overhead comparator. Count material omissions, unsupported claims, user interruptions and handoff ambiguity alongside cost. Adopt whichever reliably meets the quality floor; a custom skill is not inherently the winner.

Reproduction instructions and expected observations are in [the fixture guide](eval-fixtures/README.md). Saved outputs are preserved with path-only normalization described in the [result manifest](eval-results/manifest.json); they are examples to inspect, not golden answers.
