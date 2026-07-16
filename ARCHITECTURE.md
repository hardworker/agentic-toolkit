# agentic-toolkit — Architecture

Two skills, one design philosophy: agent output you don't have to re-check, because every claim was attacked before it reached you — and bounded token cost, because every mechanism is gated or capped.

- [**adversarial-review**](#adversarial-review) — cross-model debate review of an existing target (diff, working tree, documents).
- [**crucible**](#crucible) — end-to-end build pipeline (idea → challenged assumptions → plan → code → tests) that debates the user before it builds.

## adversarial-review

A cross-model debate review. Two independent reviewers (Claude and OpenAI Codex) review the same target, attack each other's findings, and a judge verifies every contested point in the actual files before anything is reported. The goal is a review you don't have to re-review: hallucinated findings die in cross-examination, real ones arrive with a concrete failure scenario and a fix recommendation.

### The pipeline

One iteration (report-only runs do exactly one):

```
                ┌─────────┐
                │  Scope   │  resolve what is under review (low effort)
                └────┬─────┘
             ┌───────┴────────┐
             ▼                ▼
      ┌────────────┐   ┌────────────┐
      │   Claude    │   │   Codex    │      independent reviews,
      │   review    │   │   review   │      neither sees the other
      └──────┬──────┘   └──────┬─────┘
             │    findings     │
             ▼                 ▼
      ┌────────────┐   ┌────────────┐
      │  Codex (or  │   │   Claude   │      cross-examination:
      │ self-critic)│   │  critiques │      every finding verified
      │  critiques  │   │   Codex    │      against the files,
      │   Claude    │   │            │      missed issues added
      └──────┬──────┘   └──────┬─────┘
             └───────┬─────────┘
                     ▼
              ┌────────────┐
              │  Synthesis  │   judge (high effort): merges duplicates,
              │    judge    │   re-verifies disputed high/medium findings
              └──────┬──────┘   in the files itself, assigns agreement
                     ▼
              ┌────────────┐
              │   Panel     │   only for confirmed HIGHs one model raised:
              │ (as needed) │   2 refuters vote; 2/2 refuted → rejected
              └──────┬──────┘
                     ▼
              ┌────────────┐
              │    Fix      │   fix mode only: apply confirmed fixes
              │  (optional) │   (mutation-guarded), loop back to Review
              └────────────┘
```

4–6 subagents per iteration (plus 2 per uncorroborated high finding). Every stage communicates through JSON schemas (`StructuredOutput`), so nothing depends on parsing prose.

#### Scope

A low-effort agent resolves the `target` argument into a file list, a one-paragraph summary, and (for diffs) the exact `git diff` command reviewers should run. Reviewers run the diff themselves instead of having it embedded in their prompts — for a large PR this is the single biggest token saving. Targets:

| `target` | Meaning |
|---|---|
| `auto` (default) | uncommitted changes if any, else branch diff vs. the default branch |
| `working-tree` | uncommitted changes only (the prompt explicitly forbids widening to the branch diff) |
| a git ref | `git diff <merge-base(ref, HEAD)>...HEAD` |
| a dir / file paths | those files as they stand — code or documents; one pipeline for both |

An explicit `files` argument skips the scope agent entirely.

#### Review

Two reviewers get identical instructions (modulo the id prefix) and no knowledge of each other's output beyond "you will be cross-examined". They hunt two kinds of finding:

- **`defect`** — broken behavior. Requires a concrete failure scenario: *this input/state → this wrong outcome*. For documents, defects include contradictions, ambiguity an implementer can't resolve, and tasks/specs that don't cover the stated intent.
- **`design`** — the decision itself is wrong: needless complexity, wrong abstraction, fighting existing codebase patterns, an unnecessary dependency, a path that bites later. Reviewers are told to presume every major decision guilty until it survives scrutiny. Requires naming a concrete, materially better alternative — "could be nicer" without one is banned.

Every finding carries an **impact** line (blast radius in one sentence), and severity is anchored to merge impact: *high = a maintainer would block the merge*. For diff targets, reviewers may only flag issues the change **introduces or materially worsens** — anything possibly pre-existing must be checked against the merge-base first (in the PR #208 field test, pre-existing-code findings were the entire false-positive class).

Caps keep the debate bounded: ≤ 10 issues per reviewer (≤ 5 in `strict` mode), most important first, ≤ 3 sentences per description. `strict: true` raises the bar end-to-end: reviewers and judge only keep merge-blocking findings — the low-noise mode.

#### Cross-examination

Each side verifies every one of the other's findings *against the files* (plausibility judgments are forbidden) and returns per-issue verdicts — `valid` / `invalid` (with file:line proof) / `uncertain` — plus any real issues the other side missed. A design finding is `invalid` if its alternative isn't materially better or isn't feasible in this codebase.

Each critic also sees a compact `{id, file, title}` list of its own side's findings — for **duplicate-tagging only**: when the other side's issue is the same underlying one, the verdict carries `duplicateOf`, which turns the judge's duplicate-merging from a reasoning task into bookkeeping and makes `both` agreement labels reliable.

In the PR #208 field test this stage killed 3 of Codex's 10 findings with merge-base evidence (`git show` proving the flagged code pre-existed the PR) — this is the hallucination/noise filter that makes the output trustworthy.

#### Synthesis

A high-effort judge receives each finding threaded with its critic's verdict (not the raw debate documents). Verification is **tiered** so file reads go where the stakes are:

- Findings both sides raised independently (or tagged `duplicateOf`) → confirmed once, agreement `both`, duplicates merged.
- High/medium with `invalid` / `uncertain` / `uncritiqued` verdicts → the judge must open the files and verify itself before deciding.
- High/medium with `valid` verdicts → confirm unless obviously wrong.
- Low → decided on the debate record alone, no file reads: `valid` confirms, anything unvetted is rejected (precision over volume at the tier where a miss costs least).
- Confirmed design findings carry the same weight as defects — the judge may not drop them as taste.
- Every confirmed finding gets a specific, actionable `fixRecommendation` and an agreement label (`both` / `claude-only` / `codex-only`).

#### Refute panel

A single judge is a single point of failure exactly where stakes are highest, so every confirmed **high** finding that lacks cross-model corroboration (agreement ≠ `both`) gets two fresh refuter agents. Each must produce concrete file-based evidence to refute; 2/2 refuted moves the finding to `rejected`, 1/2 keeps it annotated as contested. Cost is bounded: highs are rare, and corroborated ones skip the panel entirely.

#### Fix loop (opt-in)

With `fix: true`, a fixer agent applies the confirmed recommendations (minimal, targeted; skips anything needing a product decision), then the pipeline re-reviews the now-fixed target — up to `maxIterations` (default 3). Three guards keep the loop honest:

- **Mutation guard.** The fixer must report every file it touched (`git status --porcelain`); an edit to a file no confirmed finding names stops the run as `scope-violation` for human inspection, instead of letting the next iteration bless drift.
- **Anti-anchoring memory.** Iteration 2+ reviewers receive the already-confirmed-and-fixed list and are told not to re-report those findings — fresh passes hunt what was missed instead of re-debating what was fixed (also the cheapest token cut in the loop).
- **Stagnation circuit breaker.** A fingerprint of the confirmed set (`file|title` pairs): if an iteration confirms the same set as the previous one, the run stops as `stagnant` instead of burning tokens.

#### Effort levels

`effort: low|medium|high|xhigh|max` (default `medium`) scales the whole pipeline on the same axis as `/code-review` — low/medium buy precision, high and above buy coverage:

| level | issue cap/reviewer | finding bar | reviewer & critic tier | judge tier | refute panel |
|---|---|---|---|---|---|
| `low` | 5 | merge-blocking only (strict) | `low` | `medium` | skipped, findings annotated |
| `medium` | 10 | standard | session default | `high` | 2 votes, unanimous rejects |
| `high` | 15 | wide net | `high` | `high` | 2 votes, unanimous rejects |
| `xhigh` | 20 | wide net | `xhigh` | `xhigh` | 3 votes, majority rejects |
| `max` | 25 | wide net | `max` | `max` | 3 votes, majority rejects |

"Wide net" tells reviewers to also raise suspicions they could not fully verify, labeled as such — breadth enters at the cheapest stage and the cross-examination/judge/panel chain filters it, so output precision holds while recall grows. `--strict` composes: it wins over wide-net and pins the cap at 5. Codex runner agents stay at `low` regardless (they only transcribe), and the scope agent stays at `low`.

### The Codex leg

Codex participates through a thin runner: a low-effort Claude agent writes the prompt to a temp file, executes

```
codex exec --sandbox read-only - < promptfile
```

(with `cd <repo>` when reviewing an external root, and one retry adding `--disable code_mode_host` for the Homebrew cask that ships without `codex-code-mode-host`), then transcribes Codex's answer into the stage schema *verbatim* — the runner is forbidden to add, drop, soften, or verify anything. Codex prompts end with an explicit plain-text output contract (ISSUE/VERDICT/STANCE blocks) so transcription is mechanical.

**Degradation is graceful and honest.** Any Codex failure (missing binary, stale auth, timeout) sets `codexAvailable: false` in the result rather than aborting, and the run continues single-model. Crucially, findings still never reach the judge uncontested: when Codex is down — or deliberately skipped via `--no-codex` (`codex: false`) — a fresh Claude agent with no shared context stands in as the critic ("self-critique"). Independence comes from fresh context; hostility from the prompt.

### Design decisions

- **No meta-review phase.** The original design let each reviewer answer the critique of its findings before synthesis. In practice the judge must re-verify disputed findings in the files anyway, so the rebuttal round bought little and cost two agents re-reading everything each iteration. Removing it cut agents per iteration from 8 to 4–6.
- **Reviewers pull the diff; prompts don't carry it.** Prompts carry file lists and a diff command. Each agent reads only what it needs.
- **Token cost tracks debate volume, not phase count.** Field data: 332k tokens for a solo run confirming 7 findings; 628k for a duo run on the same 66-file PR confirming 13 of 20 candidates. Budget expectations should scale with how contested the change is.
- **One pipeline for code and documents.** Document review differs only in what counts as a defect, which fits in two lines of the reviewer rules — not in a parallel mode with its own prompts and schemas. Anything document-specific goes in `focus` free text.
- **Structured output everywhere.** Schema validation retries at the tool-call layer, so a malformed agent answer self-corrects instead of corrupting the debate record.
- **`repo` argument instead of cwd assumptions.** Workflow subagents inherit the session cwd; reviewing a PR checked out elsewhere threads `git -C <repo>` through every prompt.

### Result contract

```jsonc
{
  "status": "clean | issues-found | stagnant | max-iterations | scope-violation | nothing-to-review | error",
  "target": "origin/main",
  "iterations": 1,
  "effort": "medium",
  "codexAvailable": true,
  "confirmed": [ { "id", "kind", "file", "line", "severity", "title",
                   "description", "impact", "agreement", "fixRecommendation" } ],
  "rejected":  [ { "id", "reason" } ],
  "fixed":     [ "issue ids (fix mode)" ],
  "summary":   "judge's narrative verdict"
}
```

## crucible

An end-to-end build pipeline that treats the user's idea as a set of attackable claims. Where adversarial-review challenges finished work, crucible challenges the work *before it exists* — assumptions first, then the plan, then the diff — so bad premises die at the cheapest possible point. Its design decisions are anchored in the 2024–2026 multi-agent literature; the citations below are the load-bearing ones.

### The pipeline

```
              ┌─────────┐
              │  Recon   │  map the repo; distill the idea into a brief whose
              └────┬─────┘  assumptions are explicit, one attackable claim each
       ┌───────────┼───────────┬────────────┐
       ▼           ▼           ▼            ▼
  feasibility  necessity     scope      adversary      2–4 isolated skeptics —
       └───────────┴─────┬─────┴────────────┘          no cross-talk, assumptions
                         ▼                             unattributed
                  ┌─────────────┐
                  │ Consolidate  │  judge merges attacks, verifies contested
                  └──────┬──────┘  verdicts in the files itself
                         ▼
                ══ debate gate ══   the main thread argues the challenges with
                         ▼          the user; rulings become settled
          ┌──────────┬───┴──────┐
          ▼          ▼          ▼
       minimal    robust   refactor-first     2–3 independent planners,
          └──────────┼──────────┘             forced-apart angles
                     ▼
              ┌─────────────┐
              │  Plan judge  │  scores drafts, file-verifies their claims,
              └──────┬──────┘  synthesizes ONE plan (≤ 8 tasks, test-first)
                     ▼
               ══ plan gate ══
                     ▼
              ┌─────────────┐
              │   Develop    │  sequential task agents; each sees the whole
              └──────┬──────┘  plan + prior results; per-task test evidence
                     ▼
              ┌─────────────┐   full suite → bounded fix loop (stagnation
              │ Test+Review  │   breaker) → fresh hostile reviewer → 2-vote
              └─────────────┘   refute on highs → fix confirmed → re-run suite
```

The script is phase-parameterized (`args.phase`: `surface` / `plan` / `develop` / `test` / `full`): the main thread chains invocations and holds the gates, threading each phase's output into the next via args. `full` is the no-gate mode for autonomous runs — it **halts** (`challenged`) whenever a human ruling is needed, never guesses.

### Design decisions (and the evidence behind them)

- **Debate for critique, votes for verification, never for accuracy ensembling.** Budget-matched studies show multi-agent debate loses to cheaper self-consistency for accuracy ([Reasoning in Token Economies](https://arxiv.org/abs/2406.06461)), and most of debate's measured gains are just voting ([Debate or Vote, NeurIPS 2025](https://arxiv.org/abs/2508.17536)). So crucible uses adversarial agents only where dissent itself is the product (skeptic panel, hostile reviewer) and plain 2-vote refutation where verification is (high findings) — never N agents chatting to "improve" an answer.
- **Skeptics are isolated and see unattributed assumptions.** Cross-conditioning debaters collapses diversity ([The Cost of Consensus](https://arxiv.org/html/2605.00914v1)), so the lenses never see each other; a consolidating judge merges them. And a claim marked as *the user's stated position* measurably increases agreement with it ([SycEval](https://arxiv.org/abs/2502.08177): preemptive positions raise sycophancy 61.75% vs 56.52%), so skeptics get `{id, text}` only — the consolidator alone knows which assumptions are user-stated, because a `wrong` verdict on one of those forces `proceed: "debate"`.
- **A dedicated disagree-er with a mandate.** Self-critique degenerates once a model is confident ([Degeneration-of-Thought](https://arxiv.org/abs/2305.19118)); each skeptic's prompt defines success as effective critique ("a panel that nods is a wasted panel"), forces steelman-then-attack per assumption, and maps uncertainty to `shaky`, never `holds`.
- **Best-of-N plans + a verifying judge.** Candidate generation with independent selection is the one multi-model pattern with consistent wins on real coding benchmarks ([SWE-bench leaderboard analysis](https://arxiv.org/abs/2506.17208)); planner angles are forced apart (minimal / robust / refactor-first) and the judge must open files to check the drafts' claims, because a plan naming wrong files is worse than no plan.
- **Sequential develop; no parallel implementers.** Coding parallelizes poorly and parallel workers make conflicting implicit decisions ([Cognition](https://cognition.com/blog/dont-build-multi-agents), [Anthropic's multi-agent guidance](https://claude.com/blog/building-multi-agent-systems-when-and-how-to-use-them), [MAST](https://arxiv.org/abs/2503.13657) — most multi-agent failures are coordination failures). Each task agent gets fresh context (no rot on long builds) but sees the whole plan, all completed-task summaries, and their deviations. Blocked tasks stop the run — improvising around a broken plan is how drift starts.
- **Fresh-context hostile review + default-to-refuted.** Models favor their own output ([self-preference bias](https://arxiv.org/abs/2404.13076)), so the reviewer shares no context with the builders and hunts merge-blocking findings only (reviewer over-reporting drives over-engineering). Every high finding faces 2 independent refuters needing file evidence — the same reproduction-gate philosophy as [Aardvark](https://openai.com/index/introducing-aardvark/)'s discard-on-non-reproduction.
- **Test-first ordering, hollow-test hunting.** Agents left alone write tests that assert whatever the implementation does; planners must schedule failing acceptance tests before implementation when test infra exists, and the reviewer explicitly hunts tests that cannot fail.
- **Budget is first-class.** Fan-outs scale to the workflow token budget (~70k/agent from this repo's field data, reserve-half rule so early phases can't starve later ones), every phase boundary checks `budget-exhausted` and stops cleanly, and the result reports actual per-phase spend. Multi-agent runs ~15× chat cost ([Anthropic](https://www.anthropic.com/engineering/multi-agent-research-system)) — the pipeline must know what it spent.
- **Overhead must be earned.** The SKILL.md's first rule is when *not* to run crucible: a one-sentence uncontested change gets built directly. Spec-pipeline tooling's main failure mode is ceremony on well-understood work ([waterfall-strikes-back critique](https://marmelab.com/blog/2025/11/12/spec-driven-development-waterfall-strikes-back.html)); gates sit exactly where the industry converged — after clarification, after plan (Kiro, Spec Kit, Superpowers all gate there).

### Result contract

```jsonc
{
  "status": "done | done-with-findings | challenged | blocked | test-failures | budget-exhausted | ok | error",
  "phaseRun": "surface | plan | develop | test | full",
  "brief":   { "goal", "nonGoals", "assumptions": [{ "id", "text", "source" }], "unknowns", "constraints", "acceptanceCriteria" },
  "repoMap": { "summary", "keyFiles", "conventions", "testCommand", "lintCommand" },
  "surface": { "assumptionVerdicts", "challenges": [{ "id", "severity", "title", "evidence", "counterproposal", "recommendation" }], "openQuestions", "proceed" },
  "plan":    { "goal", "tasks": [{ "id", "title", "intent", "files", "steps", "acceptance", "testPlan", "dependsOn" }], "testStrategy", "risks", "planChallenges", "rationale" },
  "taskResults": [ { "id", "status", "changedFiles", "summary", "testEvidence", "deviations" } ],
  "suite":   { "ran", "command", "pass", "failures" },
  "review":  { "findings": [{ "id", "kind", "file", "severity", "title", "description", "impact", "fixRecommendation" }], "summary" },
  "fixedFindings": [ "finding ids" ],
  "changedFiles": [ "every file the run touched" ],
  "tokens":  { "surface", "plan", "develop", "test", "total" }
}
```

Standalone phase invocations return `status: "ok"` — the build verdict belongs to `test`/`full`.

### Fallback without an orchestrator

`PLAYBOOK.md` is the same pipeline as a sequential single-loop protocol, written tool-agnostically per the [Agent Skills open standard](https://agentskills.io/specification) portability rules: no tool names, capability-conditional wording ("if your environment can spawn fresh isolated agents…"), phase artifacts persisted to `.crucible/` files as compaction-proof memory. Codex CLI discovers the same SKILL.md from `.agents/skills/` and lands on the playbook path; its native `codex review` slots in as the fresh-eyes reviewer.

### Validation

`eval/crucible-smoke.mjs` executes the actual workflow script under a stub runtime (canned agent responses, real control flow): 30 checks covering the happy path, the challenged halt, phase chaining, blocked tasks, the stagnant fix loop, refute-panel kills, finding fixes, budget floors/exhaustion, and failure surfacing. Zero tokens. Pipeline-behavior changes must keep it green; prompt-quality changes need field runs like the sibling skill's.

### Future work

- **Cross-model skeptics/judge.** Model heterogeneity is the one intervention that consistently improves debate ([Heter-MAD](https://arxiv.org/abs/2502.08788)); the sibling skill's Codex runner pattern drops in directly.
- **Adaptive refute votes.** Fixed 2-vote panels could become early-stopping ones ([Adaptive-Consistency](https://arxiv.org/abs/2305.11860): ~8× fewer samples at <0.1% loss).

## Files & distribution

```
agentic-toolkit/
├── .claude-plugin/
│   ├── plugin.json          # repo root doubles as the plugin
│   └── marketplace.json     # ...and as its own marketplace (source "./")
├── skills/
│   ├── adversarial-review/
│   │   ├── SKILL.md              # trigger description, arg table, report format
│   │   └── adversarial-review.mjs # the Workflow script (single source of truth)
│   └── crucible/
│       ├── SKILL.md              # dual-path: Workflow orchestration or playbook
│       ├── crucible.mjs          # phase-parameterized Workflow script
│       └── PLAYBOOK.md           # sequential fallback (Codex CLI, no-Workflow)
├── eval/
│   ├── README.md                # seeded-bug fixture protocol (adversarial-review)
│   ├── score.mjs                # precision/recall scoring vs a fixture manifest
│   └── crucible-smoke.mjs       # stub-runtime control-flow test (crucible)
├── ARCHITECTURE.md
├── CHANGELOG.md
└── README.md
```

Skills instruct the model to invoke the Claude Code **Workflow tool** with `scriptPath` pointing at the `.mjs` next to the SKILL.md; the script orchestrates all subagents deterministically. Install via `npx skills add hardworker/agentic-toolkit` (scans for `SKILL.md`) or `/plugin marketplace add hardworker/agentic-toolkit`. Local installs under `~/.claude/skills/<name>` are copies managed by the skills CLI — edit in this repo and refresh with `npx skills update <name> -g`, never edit the copy. For Codex CLI, the same skill directories are discoverable from `.agents/skills/` (symlink or copy) — crucible degrades to its playbook there; adversarial-review requires the Workflow tool.

Pipeline changes are validated with the `eval/` harness — seeded-bug fixtures scored for recall/precision/cost (adversarial-review) and the stub-runtime smoke test (crucible) — because the research is clear that multi-agent protocol changes don't universally help and must be measured.
