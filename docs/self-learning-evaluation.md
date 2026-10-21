# Self-learning end-to-end evaluation

Date: 2026-10-20. Evaluated self-learning 0.1.1 with Codex CLI 0.155.1 and Claude Code 2.1.300. The feature completed a real native-host loop on synthetic CI data: capture, detached synthesis, publication, recall in both agents, explicit feedback, withdrawal, and a later proposal revision.

This demonstrates working automation and useful output on a controlled fixture. It does not establish lower CI latency, time saved on real projects, or a general improvement rate.

## Method

`tests/e2e_self_learning.py --live` installs the actual runtime and hooks into a private test home and learning store. It launches authenticated native Claude and Codex sessions against a disposable project. An observer forwards each installed hook unchanged and saves its input and output. Neither the harness nor the source agents manually invoke reflection, publication, context management or feedback commands. The only test configuration changes shorten the reflection interval, cap the store at two reflection attempts, and select Claude for the feedback reflection.

The fixture contains an executable `ci_probe.py` and three CI runs:

| Run | Queue | Execution | Reporting | Interpretation |
|---|---:|---:|---:|---|
| 101 | 22 s | 480 s | 366 s | Reporting retries after comment API throttling |
| 202 | 19 s | 510 s | 394 s | Same measured reporting pattern |
| 303, held out | 300 s | 177 s | 27 s | Queue dominates wall time; reporting has no retries |

Job baselines are 140, 145 and 150 seconds; reporting baselines are 27, 30 and 33 seconds. No queue baseline or other individual-step baselines are supplied. That omission tests whether generated guidance and its consumer invent comparisons.

Codex authentication is referenced without copying or printing it. Claude uses its normal authentication while source settings load only the isolated hooks. The harness reviews its generated hook commands and uses an invocation-only Codex hook-trust bypass. Normal production hook trust remains a separate user setup step. These tests do not verify an already-open desktop chat reloading changed hooks.

## Observed results

The completed native pass recorded seven host invocations and 28 hook events: `SessionStart`, `UserPromptSubmit`, `Stop` and `SessionEnd` on every invocation. Fourteen captured snapshots finished, the queue settled, and exactly two background reflection attempts completed. Source session invocations took 12 and 21 seconds; the remaining native invocations took 8–30 seconds, excluding background reflection. No resident worker or recursive reflection was needed. The probe source remained unchanged.

| Check | Observed result |
|---|---|
| One session | Evidence captured; zero model reflections |
| Second host session | Both hosts executed the real probe; detached Codex reflection published one procedure and one proposal |
| Publication evidence | Exact quotations from both user sessions and observed probe results; readable artifacts with source provenance |
| Claude recall and application | Native prompt hook supplied the procedure and proposal; Claude executed the held-out run using the procedure |
| Codex recall | Native prompt hook supplied the same canonical procedure; Codex named and used its diagnostic steps |
| Project scope | A separate project's native Codex hooks returned no learned context |
| Explicit negative outcome | A controlled user message in the delivered Claude session reported harmful use; detached Claude reflection recorded the outcome and withdrew the procedure |
| Fresh Codex prompt | The harmful procedure was absent; no active replacement skill was created under another slug |
| Revision behavior | The existing proposal advanced to revision 2 with queue/step baseline coverage and a false-alarm guard |
| Negative model evaluation | Both actual reflection engines returned empty skills, proposals and outcomes for unrelated sessions, repeated one-session polling and injected log instructions |

The negative outcome was deliberately supplied to test withdrawal. The fixture did not experimentally demonstrate that the procedure caused a false alarm. Silence, successful CLI exits and injected context were never scored as helpful outcomes.

## Output quality assessment

The generated procedure, `danger-ci-duration-investigation`, was usable beyond memorizing the two measurements. It supplied the observed probe command with a run parameter, separated queue and execution, compared absolute excess and ratios against median baselines, checked step totals against job time, and required both timing and log evidence for reporting throttling. It explicitly warned against treating successful CI as acceptable latency, declaring missing baselines normal, and claiming a deeper API-traffic cause without investigation.

Its held-out application was the strongest quality check. Claude measured the 300-second queue, compared 177-second execution with the 145-second median, and compared 27-second reporting with the 30-second median. It rejected the earlier reporting-retry explanation because the new log showed no retries. It left queue abnormality and the exact non-reporting step regression unresolved because the necessary baselines were absent. The agent identified the missing queue/step baselines as an improvement opportunity.

The proposal, `danger-reporting-regression-detection`, specified a CI completion check, collected metrics, a comparable healthy-run baseline, an initial rule requiring both 2× median and 60 seconds excess, deduplicated incident summaries, a history-replay check, false-positive monitoring and counts of manual investigations. Thresholds were explicitly proposed policy, rather than facts established by the two runs. Detection and reducing the underlying throttling were treated as separate interventions. Reflection subsequently revised that same proposal using the third run and the reported negative outcome.

The output was useful, with remaining limits:

- The procedure emphasized reporting because that was the repeated evidence. The held-out run showed conditional use rather than blind repetition, but broader projects need more varied trials.
- The procedure initially lacked an explicit regression decision threshold. The controlled negative report was incorporated as a false-alarm guard in the proposal; the skill was withdrawn rather than silently declared repaired.
- A consumer can confuse proposed infrastructure with existing capabilities. Injected context now explicitly says to verify capabilities before using proposed tooling or baselines.
- The source assistant did not initially know that background feedback would update the store and suggested that a manual edit was needed. Context now explains automatic, budget-dependent feedback processing and forbids unconfirmed persistence claims.
- Exact-quote and independence validation cannot prove semantic support, useful alert thresholds, or causal benefit. Human review and later explicit outcomes remain necessary evidence.
- Recall uses lexical matching with a generic-word filter. It can still miss synonyms or match shared topic words; this pass does not establish semantic retrieval accuracy across a large skill library.

## Bugs found and fixed

1. Recall used all task words with an OR query. Generic verbs such as “investigate” and “compare” injected a Danger skill into login and button-color requests. Startup also loaded the newest skill without a task. Recall now ignores generic request words, waits for meaningful terms, and leaves unrelated proposal notifications available for a relevant prompt.
2. The outcome boundary accepted the last row already present when guidance was delivered. Automatic feedback now requires a source row strictly after that snapshot. Regression coverage includes equality at the boundary.

Nineteen deterministic regression tests pass. The live positive pass used these two fixes. The two additional context explanations were added after reviewing the source-agent answers, then checked through a targeted native recall rather than repeating the whole model suite.

## Reproduction and evidence

See the [operating guide](self-learning.md#verification) for commands. Native model tests are opt-in, require authenticated CLIs, and retain private evidence in the output directory. Inspect `initial-artifacts.json`, `report.json`, hook receipts, and the host answer files for the positive pass; inspect the two engine-specific JSON files for the negative pass. Model wording and artifact slugs can vary between runs, so an assertion pass must still be accompanied by output review.

The harness requires Codex file-based authentication. It uses short CI fixtures, caps reflection at two calls, and gives Claude invocations a $1 budget each; source and negative-evaluation calls also consume provider usage. On failure, inspect the retained private logs before retrying. Do not commit reports containing local paths or session identifiers.
