# agentic-toolkit — Architecture

Two debate pipelines built on one design philosophy — agent output you don't have to re-check, because every claim was attacked before it reached you, at bounded token cost because every mechanism is gated or capped — plus two utility skills that share only the "verify before reporting" half. Both pipelines are pure prose: a SKILL.md that spawns its own agents, no orchestrator script between them.

- [**adversarial-review**](#adversarial-review) — cross-model debate review of an existing target (diff, working tree, documents). One SKILL.md, no script.
- [**crucible**](#crucible) — end-to-end build pipeline (idea → grilling → challenged assumptions → plan → code → verify) that debates the user before it builds. Same shape.
- [**session-migration**](#session-migration) — finds any past session (desktop or terminal, any account) and moves it to the surface you want. No subagents; a store-format tool.
- [**cf-access**](#cf-access) — keeps CLI tools, Node clients and long-running MCP servers authenticated to Cloudflare Access–gated hosts. No subagents; a credential-plumbing tool.

## adversarial-review

A cross-model debate review. Two independent reviewers (Claude and OpenAI Codex) review the same target and then argue about their findings until they agree or deadlock; a judge verifies what survives in the actual files before anything is reported. The goal is a review you don't have to re-review: hallucinated findings die in the argument, real ones arrive with a concrete failure scenario and a fix recommendation.

It is a **plain skill**: SKILL.md is the entire pipeline and the main agent loop executes it, spawning one subagent per debate role and shelling out to the Codex CLI directly. Only Claude Code has been exercised; a runtime that can spawn fresh agents should run it, and where only one model is available the debate structure survives but the cross-model half does not.

### The pipeline

```
             ┌────────────┐
             │   Scope    │    a cheap agent: file list, summary, diff command
             └──────┬─────┘
             ┌──────┴─────────┐
             ▼                ▼
      ┌────────────┐   ┌────────────┐
      │   Claude   │   │   Codex    │      independent reviews,
      │  subagent  │   │ codex exec │      neither sees the other
      └─────┬──────┘   └─────┬──────┘
            ▼                ▼
      ┌────────────┐   ┌────────────┐
      │  each side │   │  each side │  ◀─┐  round 1: verdicts on the
      │  attacks,  │   │  answers,  │    │  other side's findings
      │  concedes  │   │  re-judges │    │  rounds 2+: only what is
      └─────┬──────┘   └─────┬──────┘    │  still disputed
            └───────┬────────┘───────────┘  until agreed, stuck, or capped
                    ▼
             ┌────────────┐
             │ Synthesis  │    judge: arbitrates deadlocks, re-verifies
             │   judge    │    in the files, confirms
             └────────────┘
```

Scope is one cheap agent; the optional fix loop after the judge is one more. That is 4 subagents plus 2 Codex calls for a debate that settles in one round, 2 calls per extra round, and 1 agent with `--fix`. Every stage returns a JSON-only answer against a shape stated in its prompt — one shared contract for both legs, so nothing depends on parsing prose.

The main thread is strictly an orchestrator: it owns the bookkeeping — whose finding is whose, what is still disputed, whether a round moved anything — and never reads the target or takes a side. This is why scope is an agent rather than a few git commands on the main thread. Resolving a target is trivial work, but doing it inline puts the diff in the one context that survives the whole run, and "run git but don't read what it prints" is a rule rather than a boundary. One target argument covers uncommitted changes, a branch diff, or a set of paths — code and documents alike.

Reviewers hunt two kinds of finding, each with an evidence requirement that is what makes the output trustworthy. A **`defect`** requires a concrete failure scenario — *this input/state → this wrong outcome*; in documents that includes contradictions, ambiguity an implementer can't resolve, and tasks that don't cover the stated intent. A **`design`** finding requires naming a concrete, materially better alternative — reviewers presume every major decision guilty until it survives scrutiny, but "could be nicer" without an alternative is banned. Severity is anchored to merge impact: *high = a maintainer would block the merge*.

Round 1 of the debate is cross-examination: each side verifies every one of the other's findings *against the files* — plausibility judgments are forbidden — returning `valid` / `invalid` (with file:line proof) / `uncertain`, plus any issues the other side missed. This is the hallucination filter, and the one stage with a measured kill rate: in the PR #208 field test it killed 3 of Codex's 10 findings with `git show` merge-base evidence.

Later rounds run only on what is still disputed, and only two moves are legal: concede, citing the file evidence that changed your mind, or defend with evidence you have not already given. Deferring to the other reviewer is explicitly not a resolution, and repeating a claim without new evidence is declared a deadlock rather than an argument — the two rules that keep a convergence loop from converging on whoever argues hardest. The debate stops when nothing is disputed, when a round moves nothing, or at `--rounds` (default 3).

The judge then receives each surviving finding threaded with its final verdict and how it settled. Verification is **tiered** so file reads go where the stakes are: every high is opened and checked, and one nobody independently corroborated must survive an attempt to refute it; mediums ride on their verdict unless deadlocked; lows are decided on the record alone, where a miss costs least. Two reviewers landing on the same finding independently is the strongest signal in the record — agreement reached *during* the debate is not the same thing, and the judge is told to treat it as one reviewer's finding that survived an argument. Deadlocks are the judge's to arbitrate: both sides spent their evidence and neither moved, so only the files will settle it. Confirmed design findings carry the same weight as defects — the judge may not drop them as taste.

With `--fix`, a fixer applies the confirmed recommendations and the pipeline re-reviews, up to `--iterations` (default 3). Three orthogonal guards keep the loop honest: a **mutation guard** stops the run as `scope-violation` when the fixer touches a file no finding names, instead of letting the next iteration bless drift; **anti-anchoring memory** hands iteration 2+ the already-fixed list so fresh passes hunt what was missed; and a **stagnation fingerprint** of the confirmed set stops a loop that is confirming the same things twice.

`--effort low|medium|high` scales the pipeline on the same axis as `/code-review` — low buys precision, high buys coverage — moving the per-reviewer issue cap, the finding bar, and the models together. "Wide net" at `high` tells reviewers to also raise labeled suspicions: breadth enters at the cheapest stage and the cross-examination/judge chain filters it. The preset table lives in [SKILL.md](skills/adversarial-review/SKILL.md), which executes it.

### The Codex leg

The main thread runs Codex itself, writing the stage prompt and its JSON schema to temp files:

```
codex exec --sandbox read-only -C <repo> --output-schema <schema> -o <answer.json> - < promptfile
```

`-o` plus a redirect of the rest keeps Codex's reasoning transcript out of the orchestrator's context — the one context that must survive every iteration — and `--output-schema` states the expected answer shape, though an unparseable answer is still handled as a failed leg. Codex's answer is passed on **verbatim**: nothing added, dropped, softened or verified.

**Degradation is graceful and honest.** Any Codex failure (missing binary, stale auth, timeout) marks `codexAvailable: false` in the reported result rather than aborting, and the run continues single-model. Crucially, findings still never reach the judge uncontested: when Codex is down — or deliberately skipped via `--no-codex` — a fresh Claude agent with no shared context stands in as the critic ("self-critique"). Independence comes from fresh context; hostility from the prompt.

### Design decisions

- **A plain skill, not an orchestrator script.** SKILL.md is the pipeline, so there is one file, no Workflow tool and no multi-agent opt-in, and the Codex runner agents that existed only because a Workflow stage can only be an agent are gone — the main thread shells out itself, so Codex's answers reach the judge verbatim instead of through a transcription. Two things are genuinely worse for it: the loop guards are instructions rather than code, and a malformed Claude-leg answer is re-asked rather than schema-retried. The scope agent survived the conversion for the opposite reason — see below.
- **Scope is an agent, though it is only git.** The obvious simplification is to resolve the target on the main thread, which already has git; it was written that way and reverted. The scope stage exists for context isolation, not for intelligence: inline, the diff lands in the one context that lives for the whole run, and the orchestrator's "never review the target" invariant degrades from a boundary into an instruction it has to be trusted to follow while looking at the change. A cheap agent buys the invariant back, and a summary written from the actual diff rather than from paths and a `--stat`.
- **A rebuttal round, but only on disputes.** 1.0.0 removed a meta-review phase that made *every* finding take a rebuttal round, cost two agents re-reading everything each iteration, and left the judge re-verifying in the files anyway. Scoping the loop to what is actually contested is what makes it affordable this time: sides that agree exchange nothing, so a one-round debate costs what cross-examination alone used to. The evidence rules above are not decoration — cross-conditioned debaters converge on agreement rather than truth ([The Cost of Consensus](https://arxiv.org/html/2605.00914v1)) and most measured gains from debate turn out to be voting ([Debate or Vote](https://arxiv.org/abs/2508.17536)), so a loop that rewards yielding would buy the wrong thing. Unmeasured, like everything else here.
- **Refutation is the judge's job, not a panel's.** A separate refute panel voted on every uncorroborated high finding. Its refuters saw only the finding, never the critic's reasoning or the debate record, so two low-context agents could overrule the one agent that had seen everything — and its vote threshold (`floor(votes/2)+1`) made rejection *easier* at higher effort, where wide-net also makes findings more numerous. It was never measured, and the only uncorroborated high in the field record was real (the `codex-only` privilege-confinement finding the Claude leg missed twice). One line in the judge's tiering does the same work: on a high only one side raised, spend the file read trying to refute it.
- **Reviewers pull the diff; prompts don't carry it.** Prompts carry file lists and a diff command, so each agent reads only what it needs and the same review works on a 3-file and a 66-file change.
- **Token cost tracks debate volume, not phase count.** Field data (1.x, PR #208): 332k tokens for a solo run confirming 7 findings; 628k for a duo run on the same 66-file PR confirming 13 of 20 candidates. 2.0.0 has not been measured. Budget expectations should scale with how contested the change is.
- **One pipeline for code and documents.** Document review differs only in what counts as a defect, which fits in two lines of the reviewer rules — not in a parallel mode with its own prompts and schemas. Anything document-specific goes in `focus` free text.
- **JSON-only stage answers, one contract for both legs.** Every stage prompt ends with the exact shape it must return and nothing else — less to keep in sync than a schema on one side and a text format on the other, and it keeps the debate record machine-readable.
- **One depth knob.** `--effort` is the only dial; `--strict` and `xhigh`/`max` survive as aliases rather than as levels, because a second spelling of the same idea has to be arbitrated against the first every time both appear.

### Result contract

Reported as prose and written once to a temp file at the end of the run:

```jsonc
{
  "status": "clean | issues-found | stagnant | max-iterations | scope-violation | nothing-to-review | error",
  "target": "origin/main",
  "iterations": 1,
  "rounds": 2,
  "effort": "medium",
  "codexAvailable": true,
  "confirmed": [ { "id", "kind", "file", "line", "severity", "title", "description",
                   "agreement", "settled", "fixRecommendation" } ],
  "rejected":  [ { "id", "reason" } ],
  "conceded":  [ { "id", "title" } ],
  "fixed":     [ "issue ids (fix mode)" ],
  "summary":   "judge's narrative verdict"
}
```

## crucible

An end-to-end build pipeline that treats the user's idea as a set of attackable claims. Where adversarial-review challenges finished work, crucible challenges the work *before it exists* — the user first, then the assumptions, then the plan, then the diff — so bad premises die at the cheapest possible point. Its design decisions are anchored in the 2024–2026 multi-agent literature; the citations below are the load-bearing ones.

### The pipeline

```
              ┌─────────┐
              │  Grill   │  ≤4 design-changing questions per round, ≤2 rounds,
              └────┬─────┘  no agents yet; answers become user assumptions
                   ▼
              ┌─────────┐
              │  Recon   │  isolated read-only agent: map the repo; distill the
              └────┬─────┘  idea into a brief of attackable claims
       ┌───────────┼───────────┬────────────┐
       ▼           ▼           ▼            ▼
  feasibility  necessity     scope      adversary      2–4 isolated skeptics —
       └───────────┴─────┬─────┴────────────┘          no cross-talk, assumptions
                         ▼                             unattributed
                  ┌─────────────┐
                  │ Consolidate  │  main loop merges attacks, verifies contested
                  └──────┬──────┘  verdicts in the files itself
                         ▼
                  ┌─────────────┐  one agent tries to refute each challenge in
                  │   Defend     │  the files; killed ones never reach the user,
                  └──────┬──────┘  `needs-user` calls always do
                         ▼
                ══ debate gate ══   the main loop argues the survivors with
                         ▼          the user; rulings become settled
          ┌──────────┬───┴──────┐
          ▼          ▼          ▼
       minimal    robust   refactor-first     2–3 competing drafts,
          └──────────┼──────────┘             forced-apart angles
                     ▼
              ┌─────────────┐
              │  Plan judge  │  scores drafts, file-verifies their claims,
              └──────┬──────┘  synthesizes ONE plan (≤ 8 tasks, test-first)
                     ▼
               ══ plan gate ══
                     ▼
              ┌─────────────┐
              │   Develop    │  sequential, one task at a time against the whole
              └──────┬──────┘  plan + prior results; per-task test evidence
                     ▼
              ┌─────────────┐   ⟳ suite → fix failures → two fresh reviewers on
              │    Verify    │   the diff: correctness ∥ simplification → refute
              └─────────────┘   → fix ⟳ until green and clean; cap + stagnation
```

No orchestrator: the main loop runs the phases, holds the gates, and spawns isolated agents only where isolation is the mechanism (recon, each lens, the defender, each review round). Phase artifacts — `brief.md`, `challenges.md`, `plan.md`, `progress.md` — are written to the session scratchpad or `~/.crucible/<repo>/<timestamp>/`, never into the working tree the reviewer inspects; they exist for compaction recovery, and in the verify loop for resumption (below). `--auto` is the no-human mode: no grill, no gates, and a **halt** (`challenged`) whenever a ruling is needed, never a guess. There is deliberately no dry-run flag: a plan-only run just stops at the plan gate, and report-only review of an existing change is the sibling skill's job.

### Design decisions (and the evidence behind them)

- **No orchestrator.** The pipeline used to exist twice — a 647-line Workflow script and a sequential playbook — and every change had to land in both. Nothing in the design needs deterministic control flow: the gates are conversations, the loops are bounded by counts a paragraph can state, and the only thing the script bought that prose can't is structured-output schemas. One SKILL.md is now the whole skill, which also means it runs wherever the Agent Skills standard does instead of only where the Workflow tool exists.
- **Debate for critique, votes for verification, never for accuracy ensembling.** Budget-matched studies show multi-agent debate loses to cheaper self-consistency for accuracy ([Reasoning in Token Economies](https://arxiv.org/abs/2406.06461)), and most of debate's measured gains are just voting ([Debate or Vote, NeurIPS 2025](https://arxiv.org/abs/2508.17536)). So crucible uses adversarial agents only where dissent itself is the product (skeptic panel, hostile reviewer) and plain refutation where verification is (the defender on challenges, refute votes on high findings) — never N agents chatting to "improve" an answer.
- **Grill the human before spending a token.** The cheapest place to kill a bad premise is the sentence that states it, and the panel can only attack claims the brief contains — a vague brief buys four agents' worth of attacks on nothing. So Phase 0 is a bounded interrogation (≤4 design-changing questions, ≤2 rounds) whose answers enter the brief verbatim as `source: user`. It runs before recon, not after, because a clarified idea changes what recon should even map.
- **Recon is delegated, everything downstream isn't.** Mapping a repo is the largest read of the run and its output is one page; running it in the main loop would spend the context that has to survive to the last verify round. It goes to an isolated read-only agent. The main loop then argues the debate gate having read nothing first-hand — acceptable because every challenge is file-cited, so it opens the two or three files a ruling actually turns on.
- **A defender between the panel and the user.** Skeptics are paid to attack, which means some attacks are wrong; handing all of them to the user makes the user the refuter. One agent takes the consolidated list and tries to kill each challenge in the files — refutation, the verification pattern above, not another round of debate. Product and priority calls (`needs-user`) are exempt however well argued: an agent's job is to check evidence, not to decide what the software should be for.
- **Skeptics are isolated and see unattributed assumptions.** Cross-conditioning debaters collapses diversity ([The Cost of Consensus](https://arxiv.org/html/2605.00914v1)), so the lenses never see each other; a consolidating judge merges them. And a claim marked as *the user's stated position* measurably increases agreement with it ([SycEval](https://arxiv.org/abs/2502.08177): preemptive positions raise sycophancy 61.75% vs 56.52%), so skeptics get `{id, text}` only — the consolidator alone knows which assumptions are user-stated, because a `wrong` verdict on one of those forces `proceed: "debate"`.
- **A dedicated disagree-er with a mandate.** Self-critique degenerates once a model is confident ([Degeneration-of-Thought](https://arxiv.org/abs/2305.19118)); each skeptic's prompt defines success as effective critique ("a panel that nods is a wasted panel"), forces steelman-then-attack per assumption, and maps uncertainty to `shaky`, never `holds`.
- **Best-of-N plans + a verifying judge.** Candidate generation with independent selection is the one multi-model pattern with consistent wins on real coding benchmarks ([SWE-bench leaderboard analysis](https://arxiv.org/abs/2506.17208)); planner angles are forced apart (minimal / robust / refactor-first) and the judge must open files to check the drafts' claims, because a plan naming wrong files is worse than no plan.
- **Sequential develop; no parallel implementers.** Coding parallelizes poorly and parallel workers make conflicting implicit decisions ([Cognition](https://cognition.com/blog/dont-build-multi-agents), [Anthropic's multi-agent guidance](https://claude.com/blog/building-multi-agent-systems-when-and-how-to-use-them), [MAST](https://arxiv.org/abs/2503.13657) — most multi-agent failures are coordination failures). Implementation stays in the main loop, one task at a time against the whole plan, with `progress.md` as the coordination record (files, test evidence, deviations) so a compaction mid-build costs nothing. Blocked tasks stop the run — improvising around a broken plan is how drift starts.
- **Fresh-context hostile review, looped to convergence.** Models favor their own output ([self-preference bias](https://arxiv.org/abs/2404.13076)), so each review runs in an agent that sees only the diff and the plan, and hunts merge-blocking findings only (reviewer over-reporting drives over-engineering). Every high finding faces independent refuters needing file evidence — the same reproduction-gate philosophy as [Aardvark](https://openai.com/index/introducing-aardvark/)'s discard-on-non-reproduction. One shot was the 1.x weakness: a fix introduces its own defects and nobody looked again. Suite and review are now one loop that repeats until a round comes back green and clean, bounded by the effort cap and a stagnation breaker — identical failures or findings twice means report, not grind.
- **The verify loop is a [Ralph loop](https://ghuntley.com/ralph/): its state is a file, not the agent's memory.** A loop described as prose exits when the agent believes it is finished, which is the same failure class as the skipped skeptic panel — after one round of fixes, "verified" is an easy thing to believe, and a compaction anywhere inside the loop erases the round count, the declined findings and last round's failures at once. So each pass reads the `## Verify` section of `progress.md` first, appends its round record (number, suite result, findings raised/confirmed/declined/fixed) *before* evaluating anything, and then checks three named exits — `clean`, `capped`, `stagnant` — against what it just wrote. None fires, the procedure runs again from the top; the report names which one did. This buys resumption the other artifacts deliberately don't have: a fresh context can pick the loop up mid-flight, because everything the next pass needs is on disk. The cheap part is that it needs no new artifact — `progress.md` was already the build's coordination record and already survives compaction, so the loop just writes its own section of it.
- **Simplification is a review angle, not a phase — and it reviews architecture, not just lines.** Everything upstream pushes toward addition: skeptics raise risks, reviewers request fixes, fix rounds add guards. Nothing in the pipeline ever removed a line, and the accumulated result is exactly the over-engineering review is meant to prevent. So every verify round reviews the diff twice over, from opposite ends — correctness (what is broken) and simplification (what should not exist) — as two separate agents, because one reviewer holding both mandates dilutes into neither, the same lens-per-agent rule the skeptic panel runs on. The simplification mandate works at two altitudes: surface waste (dead code the change introduced, one-caller indirection, speculative options), and over-built structure, attacked down a YAGNI ladder — does the construct need to exist at all, does the repo already have the helper it reimplements (the most common agent slop: rewriting what sits a few files over), does the stdlib or platform cover it, would plain code beat the abstraction. Every finding must name the concrete smaller shape with the same behavior; "rewrite it nicer" is not a finding. Keeping the angle inside the loop means the deletions are verified by the next round's suite and reviewer rather than by a post-hoc pass whose only check is the suite; the cost is bounded by the same round cap. Simplifications face the same refutation gate — one that would change behavior, undo a confirmed fix, reach outside the diff, or remove a construct the files prove is load-bearing dies there — and a declined finding is recorded, never re-raised.
- **Test-first ordering, hollow-test hunting.** Agents left alone write tests that assert whatever the implementation does; planners must schedule failing acceptance tests before implementation when test infra exists, and the reviewer explicitly hunts tests that cannot fail.
- **Caps, not a budget object.** The Workflow budget API went with the script, so token discipline is stated instead of computed: ≤10 assumptions, ≤8 tasks, ≤6 findings per review round, one page per artifact, read only what a step needs. The counts that used to scale with remaining budget now come from the effort level alone. Multi-agent runs cost ~15× chat ([Anthropic](https://www.anthropic.com/engineering/multi-agent-research-system)), which is why every fan-out here is a fixed small number rather than "as many as it takes".
- **Three effort levels.** `low | medium | high` (default `medium`; `xhigh`/`max` accepted as aliases) drives one preset table — lenses 2/3/4, competing plans 2/2/3, defender off/on/on, verify rounds 1/2/3, refute votes 0/2/3. Both pipelines landed on three independently: five levels only paid off while a script could pass a reasoning tier through, and once depth is a model choice the top two names bought nothing but documentation. The axis stays shared with the sibling and `/code-review` — low buys precision, high buys coverage.
- **Overhead must be earned.** The SKILL.md's first rule is when *not* to run crucible: a one-sentence uncontested change gets built directly. Spec-pipeline tooling's main failure mode is ceremony on well-understood work ([waterfall-strikes-back critique](https://marmelab.com/blog/2025/11/12/spec-driven-development-waterfall-strikes-back.html)); gates sit exactly where the industry converged — after clarification, after plan (Kiro, Spec Kit, Superpowers all gate there).

### Artifacts and report

The run's state is four files, written to the session scratchpad if the environment provides one, else `~/.crucible/<repo-basename>/<timestamp>/`:

```
brief.md       goal · non-goals · assumptions table (id | claim | source) · unknowns
               · constraints · acceptance criteria · the user's settled rulings
challenges.md  verdict per assumption · surviving challenges (evidence,
               counterproposal, recommendation) · open questions
plan.md        ≤8 tasks (id | files | steps | acceptance | test plan | dependsOn)
               · test strategy · risks
progress.md    per task: files changed, test evidence, deviations
```

They exist for compaction recovery — re-read, never recalled — and stay out of the working tree so the reviewer's `git diff` is exactly the change. The final report is prose: status (`done` / `done-with-findings` / `challenged` / `blocked`), the debate record (grill answers, each challenge and its ruling, one line per defender-killed challenge), tasks and deviations, suite command and result, verify rounds run, correctness findings fixed vs remaining with `file:line`, what the simplification angle removed or was declined, and the run directory.

### Portability

Written tool-agnostically per the [Agent Skills open standard](https://agentskills.io/specification): no tool names, and a single-loop fallback for every step that would otherwise use a fresh agent. That fallback is for a runtime with no spawn mechanism, and the wording has to say so — phrased as a capability condition ("if your environment can spawn fresh isolated agents…") it reads as permission, and a host whose own system prompt says *don't spawn subagents unless the user asked* resolves the tension by taking the fallback: the skeptic panel then runs inside the context it was built to be independent of, and nothing in the output shows it happened. So the ground rule states that invoking crucible **is** the user asking, restricts the fallback to a spawn that is absent or fails, and requires the report to name any phase that took it. Claude Code and Codex CLI discover the same SKILL.md and run the same pipeline; native review and simplification commands (e.g. `codex review`) slot into the verify loop's two angles where they exist.

### Validation

Field runs only. The 1.x smoke test (`eval/crucible-smoke.mjs`) executed the Workflow script's control flow under a stub runtime; with the script gone there is no control flow to execute, and prompt-quality changes were never covered by it anyway. The sibling's fixture harness would have measured exactly that; it is gone too, so both pipelines are in the same position.

### Future work

- **Cross-model skeptics/judge.** Model heterogeneity is the one intervention that consistently improves debate ([Heter-MAD](https://arxiv.org/abs/2502.08788)); the sibling skill's Codex runner pattern drops in directly.
- **Adaptive refute votes.** Fixed 2-vote panels could become early-stopping ones ([Adaptive-Consistency](https://arxiv.org/abs/2305.11860): ~8× fewer samples at <0.1% loss).

## session-migration

The odd one out: no subagents, no debate. Two mechanisms hide past work. Claude Code Desktop scopes session records by account, so an account switch strands everything created before it; and terminal sessions never get a desktop record at all. Both are invisible to the sidebar, to `list_sessions` and to `search_session_transcripts`. The skill is a locator over every store plus routes between them, and its design work was reading the desktop app's own store and `app.asar` loader instead of guessing at the format.

### What the app actually does

```
~/Library/Application Support/Claude/claude-code-sessions/<accountId>/<orgId>/local_<uuid>.json   ← account-scoped record
~/.claude/projects/<slug(cwd)>/<cliSessionId>.jsonl                                               ← transcript, account-agnostic
~/.claude/jobs/<first-8-of-cliSessionId>/{state.json,timeline.jsonl}                              ← CLI `claude agents` registry
```

Three facts drive every design decision:

1. **`LocalSessionManager` holds the records in an in-memory map in the main process**, rebuilt only on launch or an account switch. No file watcher — a record copied into the directory stays invisible until restart. This is why "just move the file" is not a complete answer.
2. **`claude://resume?session=<cliSessionId>` calls `importCliSession`**, which builds a fresh record from the transcript *in the current account* and inserts it live. This is the app's own recovery mechanism, and the only path that avoids a restart.
3. **The app's recovery scan excludes any transcript whose id appears in a record under *any* account** (`addOnDiskCliSessionIdsFromAllOrgs`). So the built-in "import CLI sessions" UI will never offer a session you still hold elsewhere — a stranded session must be reached deliberately.

Interactive desktop sessions never get a `~/.claude/jobs/` entry, so they are absent from `claude agents` under every account; `job` synthesizes one from the record plus the transcript (name, intent, result summary, token count, resume id).

### Routing, not migrating

Because the transcript is the durable artifact and the other two stores are pointers to it, most of what looks like migration is just writing the missing pointer:

| Destination | Route | Cost |
|---|---|---|
| desktop sidebar, now | `import` — the deep link | new record id, metadata reset |
| desktop sidebar, intact | `move` — relocate the record | full app restart |
| terminal | `resume` — print `claude --resume` | none; the transcript was always reachable |
| `claude agents` | `job` — synthesize the registry entry | none |

Only the desktop direction needs a decision, which is why `import` and `move` carry a tradeoff table and refuse to both run. Desktop → CLI is free.

Every route through `claude --resume` has one hard precondition: no background agent may hold the session. The claim is a live listener on `/tmp/cc-daemon-<uid>/*/rv/<first-8-of-cliSessionId>.sock`, and while it exists the resume exits 1 — which the desktop app reports as "Claude Code crashed" over a record it already created. Crucially the claim is not reflected in the job's `state.json`: a job reading `done` / `idle` can still own the socket, and the agents view files that job under completed and shows no Stop control, so nothing in either UI looks running. `import` and `resume` therefore preflight the socket and name the holding pids; `--force` is deliberately powerless against it, because the refusal comes from the CLI. `write_job` preflights it as well, which covers `job` and `move` in one place: the job dir is keyed by the same `cli[:8]` as the socket, so synthesizing an entry over a live daemon would replace its `state.json` with a fabricated `done` / `idle` and strip the Stop control from the one UI that still had it.

The inventory unifies both worlds: desktop records keyed by `cliSessionId`, plus every `~/.claude/projects/*/<uuid>.jsonl` not already claimed by one, tagged `source: cli`. CLI titles come from the transcript's own `ai-title` entry and the location from its `cwd`/`gitBranch` header fields — a header-only read (first 400 lines) that costs ~1s across 160 sessions, cheap enough that no cache exists to go stale.

### Design decisions

- **Two paths, mutually exclusive.** `import` is live but produces a *new* record id (`local_<cliSessionId>`) and loses title, model and the original timestamps; `move` preserves the record whole but needs a restart. Running both yields two sidebar rows for one conversation, so each refuses when the other has run.
- **Fuzzy by default.** The trigger case is a half-remembered name, so `find` scores title, worktree, branch, cwd and — for untitled sessions — the transcript's first user message, combining sequence ratio, substring hit and token recall. Ambiguity is surfaced, never resolved by guess: top two within 0.12 prints candidates and stops.
- **Search the CLI too, always.** Scoping the inventory to desktop records was the 1.0.0 mistake: on this machine that is 15 sessions out of 162. A skill whose whole job is "find the conversation the user means" cannot skip 90% of them, and the scan is cheap enough that there is no reason to make it opt-in.
- **Nothing is destroyed.** `move` renames, `--copy` duplicates, an existing destination is refused, the running session is blocked. The single removal is a deletion tombstone (`deleted_<uuid>`, holding the deletion epoch-ms) under `--force`.
- **Never patch a loaded record.** The in-memory copy wins and overwrites disk, so renames go through `set_session_title` rather than the file.
- **Verify before reporting**, the one habit shared with the debate skills: `list_sessions` must show an imported session and `claude agents --json --all` must contain a synthesized job before success is claimed.

### Result contract

Plain stdout, not JSON schemas — the consumer is the agent's own reading, and every mutation prints its source path, destination path and the refresh the user must perform. `--dry-run` on every mutating subcommand prints exactly that report and writes nothing.

## cf-access

The other utility skill, and the only one that installs a background process. The problem is narrow and unfixable at the client: an Access app whose policy allows only an IdP has no service-token path, so the JWT can only come from a browser SSO round-trip, and it lives about a day. Every client that reads its credential once at startup — most MCP servers, any daemon taking a header from env — therefore works for a day and then fails with a login redirect that looks nothing like an auth error. Three layers, each solving a different amount of "the client cannot be changed".

```
cf-access              broker: mint / cache / renew, one place that knows how
   ↑ per invocation                    ↑ per request
shell, curl, MCP launchers      cf-access-proxy ── 127.0.0.1:8780 (dynamic, header names upstream)
                                        │      └─ 127.0.0.1:<port> (fixed route, any language)
                                        ↑
                           cf-access-preload.cjs (NODE_OPTIONS=--require, patches http/https/fetch)
```

### Design decisions (and the evidence behind them)

- **A broker, not per-client auth.** Every client gets either a token (`token`/`cookie`/`env`/`curl`) or a URL (proxy). Nothing else has to know that `cloudflared` exists, which is what makes a newly gated tool a config line rather than a code change.
- **Origins, never paths.** `cloudflared` caches tokens per hostname, so an app URL carrying a path silently misses the cache and re-mints forever. Every entry point truncates to the origin first.
- **`login` clears the cache before it logs in.** `cloudflared access login` returns the *cached* app token if one exists, even seconds from expiry — so a "refresh" without a purge is a no-op. The purge stashes the token to a temp dir and restores it on any exit path (including a timeout or Ctrl-C), so a browser-less machine cannot lose a still-usable token to a failed refresh.
- **Cache files are found by the token's own `aud`,** not by hostname glob: an app covered by a wildcard policy lands in a `-.<domain>-<aud>-token` file that a host-name pattern would miss.
- **Gating is learned, not configured.** The proxy sends the first request to an origin *bare*; only a redirect to `cdn-cgi/access/login` proves a token is needed. So a non-gated host never triggers an SSO attempt, and a host gated next month starts getting tokens with no config change.
- **A credential on the request beats the broker — but only if Access accepts it.** Requests carrying a service token, a `cf-access-token`, or a session cookie are forwarded untouched; the broker steps in only when Access rejects them. Both halves were learned the hard way: without pass-through, a service-token client gets its working auth replaced by an interactive login it cannot perform; without the fallback, a service token that is *not* on the app's policy hands the client a login page instead of data — and one real MCP server on this machine turned out to be in exactly that state, silently depending on an injected browser token.
- **The login deadline lives in the broker.** `cloudflared` waits for the SSO callback forever, so the bound belongs where every caller routes through — a shell, `cf-access env` launching an MCP server, the proxy — not in one caller. `cf-access` kills an unanswered login after `CF_ACCESS_LOGIN_DEADLINE` and restores the token it stashed. The proxy keeps its own deadline as well, for the different failure it owns: a child it cannot kill (below).
- **A deadline settles the promise; the kill is only cleanup.** `execFile`'s own `timeout` sends `SIGTERM`, which `cloudflared` ignores while holding the pipe open — measured: a "120s" login blocked a request for 9 minutes, and `detached: true` does not reliably create a killable process group (observed `PGID` inherited from the parent, so `kill(-pid)` is `ESRCH`). The timer therefore resolves the mint itself, and a late success still populates the cache for the client's retry.
- **Bounded hold instead of an unbounded wait.** A request may wait `CF_ACCESS_HOLD` seconds (default 20, chosen to sit under the common 30s MCP client timeout) and is then answered `511` while the login continues in the background — so the human tap is not raced against a client timeout it would always lose; the retry simply finds a token.
- **The allowlist is a domain suffix list, not an app list** — the same reason, and it doubles as the security boundary: the dynamic port would otherwise be an open forwarder on loopback for anything running as the user. Missing file means allow nothing, never a built-in default domain. Because it *is* the boundary it has exactly one implementation (`cf-access-hosts.cjs`, required by both the proxy and the preload): two copies would drift into either half of the failure — traffic the proxy refuses, or an open forwarder. It is re-read at most every 2s rather than watched, so a preloaded short-lived process still exits (an `fs.watchFile` in a `NODE_OPTIONS` shim would hold every Node process open).
- **Single-flight minting with a login cooldown.** A stale-token stampede collapses into one mint per origin, and a browser login is rate-limited to once a minute — without it a burst of failing requests stacks up SSO tabs.
- **Bodies are buffered** so the token retry replays a POST byte-for-byte instead of failing it.
- **The preload refuses to patch the proxy itself** (`argv[1]` check). The proxy is the one process that must reach the real hosts; patching it would aim it at its own port forever.
- **Config is polled (`watchFile`), and a bad config never exits.** Editors replace files rather than writing in place, which breaks an inode-bound watcher; and under launchd `KeepAlive` an exit-on-bad-config is a restart loop, so malformed lines are logged and the good routes keep serving.
- **The launchd plist carries an explicit `PATH` and `CF_ACCESS_BIN`.** launchd starts with a bare environment, and the proxy shells out to `cf-access`, which needs both `node` and `cloudflared` — the most common "it works in my shell" failure. `install.sh` writes the plist with the `node` it detected rather than shipping a fixed path. Every other `CF_ACCESS_*` knob present in the environment is copied in the same way, because the plist is the daemon's whole environment: a knob the installer does not carry is one the daemon cannot see, however well documented it is. Values already in the plist survive a plain re-run; unset knobs are simply absent, leaving the default owned by the runtime.

### Result contract

HTTP status codes and one log line per event, not JSON: the consumers are ordinary clients. The proxy originates `511` (no token — run `login`), `403` (host not in the allowlist), `508` (upstream is the proxy itself), `400` (missing upstream header, which is also the health check), `502` (transport). `install.sh status` is the single diagnostic — links, every file in the config dir, `cloudflared`, the resolved SSO browser (asked of `cf-access browser`, so it cannot disagree with what a login will do), daemon state, port liveness, per-app token TTL — because "no token", "daemon down", "host not allowed" and "not installed" all look identical from the client side.

## Files & distribution

```
agentic-toolkit/
├── .claude-plugin/
│   ├── plugin.json          # repo root doubles as the plugin
│   └── marketplace.json     # ...and as its own marketplace (source "./")
├── skills/
│   ├── adversarial-review/
│   │   └── SKILL.md              # the whole pipeline: args, stage prompts, guards, report
│   ├── crucible/
│   │   └── SKILL.md              # the whole pipeline: phases, gates, caps, report
│   ├── session-migration/
│   │   ├── SKILL.md              # store model, the two recovery paths, safety rules
│   │   └── ccd_sessions.py       # locator + import/move/job (no orchestration)
│   └── cf-access/
│       ├── SKILL.md              # three layers, wiring patterns, troubleshooting
│       ├── cf-access             # token broker (sh)
│       ├── cf-access-proxy       # localhost fronts, token injection (node)
│       ├── cf-access-preload.cjs # NODE_OPTIONS shim for unmodifiable Node clients
│       ├── cf-access-hosts.cjs   # the suffix allowlist, shared by proxy and preload
│       ├── install.sh            # symlinks + config seed + launchd agent; status/uninstall
│       └── apps.example, hosts.example, browser.example
├── ARCHITECTURE.md
├── CHANGELOG.md
└── README.md
```

Both pipelines are pure prose now: each SKILL.md is its own pipeline, spawning isolated agents where they earn it, with no script to orchestrate them. session-migration is plain Bash over the Python script beside its SKILL.md — macOS only. cf-access is the same shape, except its scripts are also **installed** outside the skill: `install.sh` symlinks them into a bin dir (default `~/.claude/bin`) and loads a launchd agent, so the skill directory stays the single source of truth while the daemon and every wired client run from stable paths. Install via `npx skills add hardworker/agentic-toolkit` (scans for `SKILL.md`) or `/plugin marketplace add hardworker/agentic-toolkit`. On this machine the local installs are symlinks into this repo — `~/.claude/skills/<name>` (Claude Code) and `~/.agents/skills/<name>` (Codex CLI) both point at `skills/<name>`, so edits go live on the next session with no update step; don't run `npx skills update` over them. Codex CLI discovers the same SKILL.md via `.agents/skills` — crucible runs there in full; adversarial-review should once its Claude Code subagent type and model names are substituted, though it has not been exercised there.

Neither pipeline has an executable surface left to test, and neither has a harness. `eval/` — the seeded-bug fixture protocol plus `score.mjs`, which scored an adversarial-review run's record for recall and false positives — was dropped: no fixture was ever built for it, so it measured nothing, and a protocol nobody has run is not validation. Both pipelines are validated by field runs. The research is clear that multi-agent protocol changes don't universally help and must be measured, which is the standard both are short of; the removed protocol is in git history for whoever builds the first fixture.
