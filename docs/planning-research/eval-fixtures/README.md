# Planning pilot fixtures

These are synthetic evaluation inputs, not production code or factual research sources. They deliberately omit information a planner must not invent. No upstream framework needs to be installed.

## Repeat the pilot

Use fresh contexts and a separate disposable directory per run. Copy the relevant fixture there. Keep the same host/model settings, task, source access, and tool permissions across compared runs; record any differences. Do not show agents the expected observations below or other outputs before they finish.

1. **Engineering baseline:** supply `engineering/REQUEST.md` and its three supporting files. Ask for the requested plan using ordinary planning, without a planning skill or subagents. Permit existing tests and read-only probes; prohibit network, installation, and source edits.
2. **Engineering candidate:** give a fresh context the same files plus `skills/grounded-plan/SKILL.md`; request standard effort. Permit the skill's bounded fresh critique, with the same source/tool limits. Freeze the plan before review. Save the plan and a receipt of sources, checks, actual review calls, and limitations.
3. **Product:** supply `product.md` with the candidate skill at lean effort. No web, users, analytics access, implementation, or additional agents. Save the plan and receipt.
4. **Research review:** supply `research.md` with the candidate skill and `--review --effort standard`. Enforce the packet's no-web/no-agents constraints. Save a separate review and preserve the original.
5. **Deep review component:** freeze the completed engineering candidate. Give one fresh critic the task, source files, and fixed plan. Give a different fresh alternative author only the task and source files. Collect both initial answers before sharing either. Follow `review.md` for material disputes; do not force disagreement to exercise the cap. This tests the review component, not a new end-to-end deep planning run.

Ask each run to record tool commands/results, source access, limitations, and review context/call counts. Record elapsed time only when measured and token/cost data only when the host exposes it. A receipt is an agent's report; corroborate important execution claims with tool results when available. Independent contexts can still share the same model and failure modes.

The engineering fixture's existing checks run without dependencies:

```sh
cd <fixture-copy>
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v
```

## Expected observations for grading

| Case | Material observations |
|---|---|
| Engineering | Discover existing reuse; distinguish sequential deduplication from durable concurrency safety; identify unused 24-hour retention versus requested seven days; address tenant boundaries and proper CSV; leave throughput unproven without measurements; distinguish proposed tests from executed checks. |
| Product | Flag support-recruitment bias, undefined 31% baseline, and unvalidated personas; respect two weeks/one engineer; require definitions and thresholds; offer smaller fallback work; do not invent demand, sample sufficiency, or launch readiness. |
| Research | A/B are one source origin; before/after counts are confounded; denominators matter; four weeks cannot directly establish annual retention; diagram puts adoption before trial; preserve original and report absent independent review. |
| Deep component | Separate initial judgments; inspect actual sources; stop if settled; report same-model limits; do not treat agreement as proof or add rounds just to meet a quota. |

Grade material omissions and unsupported claims, not heading compliance. Also record output length, unresolved decisions, interventions, and work proxies. Repeat and randomize comparisons before drawing quality/cost conclusions. The first pilot and its limits are in [evaluation.md](../evaluation.md).
