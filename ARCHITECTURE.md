# adversarial-review — Architecture

A cross-model debate review. Two independent reviewers (Claude and OpenAI Codex) review the same target, attack each other's findings, and a judge verifies every contested point in the actual files before anything is reported. The goal is a review you don't have to re-review: hallucinated findings die in cross-examination, real ones arrive with a concrete failure scenario and a fix recommendation.

## The pipeline

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
              │    judge    │   re-verifies disputed/uncritiqued findings
              └──────┬──────┘   in the files itself, assigns agreement
                     ▼
              ┌────────────┐
              │    Fix      │   fix mode only: apply confirmed fixes,
              │  (optional) │   then loop back to Review
              └────────────┘
```

4–6 subagents per iteration. Every stage communicates through JSON schemas (`StructuredOutput`), so nothing depends on parsing prose.

### Scope

A low-effort agent resolves the `target` argument into a file list, a one-paragraph summary, and (for diffs) the exact `git diff` command reviewers should run. Reviewers run the diff themselves instead of having it embedded in their prompts — for a large PR this is the single biggest token saving. Targets:

| `target` | Meaning |
|---|---|
| `auto` (default) | uncommitted changes if any, else branch diff vs. the default branch |
| `working-tree` | uncommitted changes only (the prompt explicitly forbids widening to the branch diff) |
| a git ref | `git diff <merge-base(ref, HEAD)>...HEAD` |
| a dir / file paths | those files as they stand — code or documents; one pipeline for both |

An explicit `files` argument skips the scope agent entirely.

### Review

Two reviewers get identical instructions (modulo the id prefix) and no knowledge of each other's output beyond "you will be cross-examined". They hunt two kinds of finding:

- **`defect`** — broken behavior. Requires a concrete failure scenario: *this input/state → this wrong outcome*. For documents, defects include contradictions, ambiguity an implementer can't resolve, and tasks/specs that don't cover the stated intent.
- **`design`** — the decision itself is wrong: needless complexity, wrong abstraction, fighting existing codebase patterns, an unnecessary dependency, a path that bites later. Reviewers are told to presume every major decision guilty until it survives scrutiny. Requires naming a concrete, materially better alternative — "could be nicer" without one is banned.

Caps keep the debate bounded: ≤ 10 issues per reviewer, most important first, ≤ 3 sentences per description.

### Cross-examination

Each side verifies every one of the other's findings *against the files* (plausibility judgments are forbidden) and returns per-issue verdicts — `valid` / `invalid` (with file:line proof) / `uncertain` — plus any real issues the other side missed. A design finding is `invalid` if its alternative isn't materially better or isn't feasible in this codebase.

In the PR #208 field test this stage killed 3 of Codex's 10 findings with merge-base evidence (`git show` proving the flagged code pre-existed the PR) — this is the hallucination/noise filter that makes the output trustworthy.

### Synthesis

A high-effort judge receives each finding threaded with its critic's verdict (not the raw debate documents). Rules:

- Findings both sides raised independently → confirmed once, agreement `both`, duplicates merged.
- `valid` verdicts → confirm unless obviously wrong.
- `invalid`, `uncertain`, or `uncritiqued` → the judge must open the files and verify itself before deciding. Nothing unvetted gets confirmed or rejected on faith.
- Confirmed design findings carry the same weight as defects — the judge may not drop them as taste.
- Every confirmed finding gets a specific, actionable `fixRecommendation` and an agreement label (`both` / `claude-only` / `codex-only`).

### Fix loop (opt-in)

With `fix: true`, a fixer agent applies the confirmed recommendations (minimal, targeted; skips anything needing a product decision), then the pipeline re-reviews the now-fixed target — up to `maxIterations` (default 3). A fingerprint of the confirmed set (`file|title` pairs) acts as a circuit breaker: if an iteration confirms the same set as the previous one, the run stops as `stagnant` instead of burning tokens.

## The Codex leg

Codex participates through a thin runner: a low-effort Claude agent writes the prompt to a temp file, executes

```
codex exec --sandbox read-only - < promptfile
```

(with `cd <repo>` when reviewing an external root, and one retry adding `--disable code_mode_host` for the Homebrew cask that ships without `codex-code-mode-host`), then transcribes Codex's answer into the stage schema *verbatim* — the runner is forbidden to add, drop, soften, or verify anything. Codex prompts end with an explicit plain-text output contract (ISSUE/VERDICT/STANCE blocks) so transcription is mechanical.

**Degradation is graceful and honest.** Any Codex failure (missing binary, stale auth, timeout) sets `codexAvailable: false` in the result rather than aborting, and the run continues single-model. Crucially, findings still never reach the judge uncontested: when Codex is down — or in deliberate `solo` mode — a fresh Claude agent with no shared context stands in as the critic ("self-critique"). Independence comes from fresh context; hostility from the prompt.

## Design decisions

- **No meta-review phase.** The original design let each reviewer answer the critique of its findings before synthesis. In practice the judge must re-verify disputed findings in the files anyway, so the rebuttal round bought little and cost two agents re-reading everything each iteration. Removing it cut agents per iteration from 8 to 4–6.
- **Reviewers pull the diff; prompts don't carry it.** Prompts carry file lists and a diff command. Each agent reads only what it needs.
- **Token cost tracks debate volume, not phase count.** Field data: 332k tokens for a solo run confirming 7 findings; 628k for a duo run on the same 66-file PR confirming 13 of 20 candidates. Budget expectations should scale with how contested the change is.
- **One pipeline for code and documents.** Document review differs only in what counts as a defect, which fits in two lines of the reviewer rules — not in a parallel mode with its own prompts and schemas. Anything document-specific goes in `focus` free text.
- **Structured output everywhere.** Schema validation retries at the tool-call layer, so a malformed agent answer self-corrects instead of corrupting the debate record.
- **`repo` argument instead of cwd assumptions.** Workflow subagents inherit the session cwd; reviewing a PR checked out elsewhere threads `git -C <repo>` through every prompt.

## Result contract

```jsonc
{
  "status": "clean | issues-found | stagnant | max-iterations | nothing-to-review | error",
  "target": "origin/main",
  "iterations": 1,
  "codexAvailable": true,
  "confirmed": [ { "id", "kind", "file", "line", "severity", "title",
                   "description", "agreement", "fixRecommendation" } ],
  "rejected":  [ { "id", "reason" } ],
  "fixed":     [ "issue ids (fix mode)" ],
  "summary":   "judge's narrative verdict"
}
```

## Files & distribution

```
agentic-toolkit/
├── .claude-plugin/
│   ├── plugin.json          # repo root doubles as the plugin
│   └── marketplace.json     # ...and as its own marketplace (source "./")
├── skills/
│   └── adversarial-review/
│       ├── SKILL.md              # trigger description, arg table, report format
│       └── adversarial-review.mjs # the Workflow script (single source of truth)
├── ARCHITECTURE.md
├── CHANGELOG.md
└── README.md
```

The skill instructs the model to invoke the Claude Code **Workflow tool** with `scriptPath` pointing at the `.mjs` next to the SKILL.md; the script orchestrates all subagents deterministically. Install via `npx skills add igorsova/agentic-toolkit` (scans for `SKILL.md`) or `/plugin marketplace add igorsova/agentic-toolkit`. Local development uses a symlink from `~/.claude/skills/adversarial-review` into this repo.
