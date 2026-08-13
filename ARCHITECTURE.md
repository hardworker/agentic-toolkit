# agentic-toolkit — Architecture

Two debate pipelines built on one design philosophy — agent output you don't have to re-check, because every claim was attacked before it reached you, at bounded token cost because every mechanism is gated or capped — plus two utility skills that share only the "verify before reporting" half. One pipeline is a Workflow script, the other is pure prose; the philosophy is what they share, not the machinery.

- [**adversarial-review**](#adversarial-review) — cross-model debate review of an existing target (diff, working tree, documents). Workflow-orchestrated.
- [**crucible**](#crucible) — end-to-end build pipeline (idea → grilling → challenged assumptions → plan → code → verify) that debates the user before it builds. A pure skill: one SKILL.md, no script.
- [**session-migration**](#session-migration) — finds any past session (desktop or terminal, any account) and moves it to the surface you want. No subagents; a store-format tool.
- [**cf-access**](#cf-access) — keeps CLI tools, Node clients and long-running MCP servers authenticated to Cloudflare Access–gated hosts. No subagents; a credential-plumbing tool.

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
- **`cwd` argument instead of cwd assumptions.** Workflow subagents inherit the session cwd; reviewing a PR checked out elsewhere threads `git -C <root>` through every prompt. (Legacy `repo` still maps.)

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

No orchestrator: the main loop runs the phases, holds the gates, and spawns isolated agents only where isolation is the mechanism (recon, each lens, the defender, each review round). Phase artifacts — `brief.md`, `challenges.md`, `plan.md`, `progress.md` — are written to the session scratchpad or `~/.crucible/<repo>/<timestamp>/`, never into the working tree the reviewer inspects; they exist for compaction recovery, not for resumption. `--auto` is the no-human mode: no grill, no gates, and a **halt** (`challenged`) whenever a ruling is needed, never a guess. There is deliberately no dry-run flag: a plan-only run just stops at the plan gate, and report-only review of an existing change is the sibling skill's job.

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
- **Simplification is a review angle, not a phase — and it reviews architecture, not just lines.** Everything upstream pushes toward addition: skeptics raise risks, reviewers request fixes, fix rounds add guards. Nothing in the pipeline ever removed a line, and the accumulated result is exactly the over-engineering review is meant to prevent. So every verify round reviews the diff twice over, from opposite ends — correctness (what is broken) and simplification (what should not exist) — as two separate agents, because one reviewer holding both mandates dilutes into neither, the same lens-per-agent rule the skeptic panel runs on. The simplification mandate works at two altitudes: surface waste (dead code the change introduced, one-caller indirection, speculative options), and over-built structure, attacked down a YAGNI ladder — does the construct need to exist at all, does the repo already have the helper it reimplements (the most common agent slop: rewriting what sits a few files over), does the stdlib or platform cover it, would plain code beat the abstraction. Every finding must name the concrete smaller shape with the same behavior; "rewrite it nicer" is not a finding. Keeping the angle inside the loop means the deletions are verified by the next round's suite and reviewer rather than by a post-hoc pass whose only check is the suite; the cost is bounded by the same round cap. Simplifications face the same refutation gate — one that would change behavior, undo a confirmed fix, reach outside the diff, or remove a construct the files prove is load-bearing dies there — and a declined finding is recorded, never re-raised.
- **Test-first ordering, hollow-test hunting.** Agents left alone write tests that assert whatever the implementation does; planners must schedule failing acceptance tests before implementation when test infra exists, and the reviewer explicitly hunts tests that cannot fail.
- **Caps, not a budget object.** The Workflow budget API went with the script, so token discipline is stated instead of computed: ≤10 assumptions, ≤8 tasks, ≤6 findings per review round, one page per artifact, read only what a step needs. The counts that used to scale with remaining budget now come from the effort level alone. Multi-agent runs cost ~15× chat ([Anthropic](https://www.anthropic.com/engineering/multi-agent-research-system)), which is why every fan-out here is a fixed small number rather than "as many as it takes".
- **Three effort levels.** `low | medium | high` (default `medium`; `xhigh`/`max` accepted as aliases) drives one preset table — lenses 2/3/4, competing plans 2/2/3, defender off/on/on, verify rounds 1/2/3, refute votes 0/2/3. The sibling's five levels exist because it can also dial agent reasoning tiers; with no script to pass them through, the top two levels bought one extra refute vote and two more names to document.
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

Written tool-agnostically per the [Agent Skills open standard](https://agentskills.io/specification): no tool names, capability-conditional wording ("if your environment can spawn fresh isolated agents…"), and a single-loop fallback for every step that would otherwise use one. Claude Code and Codex CLI discover the same SKILL.md and run the same pipeline; native review and simplification commands (e.g. `codex review`) slot into the verify loop's two angles where they exist.

### Validation

Field runs only. The 1.x smoke test (`eval/crucible-smoke.mjs`) executed the Workflow script's control flow under a stub runtime; with the script gone there is no control flow to execute, and prompt-quality changes were never covered by it anyway — the same limitation as the sibling skill's prompt half, which its fixture harness measures instead.

### Future work

- **Cross-model skeptics/judge.** Model heterogeneity is the one intervention that consistently improves debate ([Heter-MAD](https://arxiv.org/abs/2502.08788)); the sibling skill's Codex runner pattern drops in directly.
- **Adaptive refute votes.** Fixed 2-vote panels could become early-stopping ones ([Adaptive-Consistency](https://arxiv.org/abs/2305.11860): ~8× fewer samples at <0.1% loss).

## session-migration

The odd one out: no Workflow script, no subagents, no debate. Two mechanisms hide past work. Claude Code Desktop scopes session records by account, so an account switch strands everything created before it; and terminal sessions never get a desktop record at all. Both are invisible to the sidebar, to `list_sessions` and to `search_session_transcripts`. The skill is a locator over every store plus routes between them, and its design work was reading the desktop app's own store and `app.asar` loader instead of guessing at the format.

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
│   │   ├── SKILL.md              # trigger description, arg table, report format
│   │   └── adversarial-review.mjs # the Workflow script (single source of truth)
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
├── eval/
│   ├── README.md                # seeded-bug fixture protocol (adversarial-review)
│   └── score.mjs                # precision/recall scoring vs a fixture manifest
├── ARCHITECTURE.md
├── CHANGELOG.md
└── README.md
```

adversarial-review instructs the model to invoke the Claude Code **Workflow tool** with `scriptPath` pointing at the `.mjs` next to its SKILL.md; the script orchestrates all subagents deterministically. crucible is pure prose — its SKILL.md is the pipeline, and it spawns isolated agents itself where they earn it. session-migration is plain Bash over the Python script beside its SKILL.md — macOS only. cf-access is the same shape, except its scripts are also **installed** outside the skill: `install.sh` symlinks them into a bin dir (default `~/.claude/bin`) and loads a launchd agent, so the skill directory stays the single source of truth while the daemon and every wired client run from stable paths. Install via `npx skills add hardworker/agentic-toolkit` (scans for `SKILL.md`) or `/plugin marketplace add hardworker/agentic-toolkit`. On this machine the local installs are symlinks into this repo — `~/.claude/skills/<name>` (Claude Code) and `~/.agents/skills/<name>` (Codex CLI) both point at `skills/<name>`, so edits go live on the next session with no update step; don't run `npx skills update` over them. Codex CLI discovers the same SKILL.md via `.agents/skills` — crucible runs there in full; adversarial-review requires the Workflow tool.

adversarial-review's pipeline changes are validated with the `eval/` harness — seeded-bug fixtures scored for recall/precision/cost — because the research is clear that multi-agent protocol changes don't universally help and must be measured. crucible has no executable surface left to test; its changes are validated by field runs.
