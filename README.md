# agentic-toolkit

Personal agent toolkit. See [ARCHITECTURE.md](ARCHITECTURE.md) for how the debate pipeline works and [CHANGELOG.md](CHANGELOG.md) for history. Currently one skill:

## adversarial-review

Adversarial Claude-vs-Codex debate review of any target — branch diff, working tree, or documents (specs, proposals, plans). Hunts real defects **and** challenges design decisions, approaches, and implementation paths.

Pipeline (one iteration, 4–6 subagents):

```
Scope → [Claude review ∥ Codex review] → [cross-examination ∥] → Synthesis judge → (Fix loop)
```

- Both reviewers work independently, then attack each other's findings.
- The synthesis judge re-verifies every disputed finding in the actual files before confirming.
- Findings are typed: `defect` (concrete failure scenario required) or `design` (concrete better alternative required).
- Codex leg degrades gracefully — if the Codex CLI is missing/unauthenticated, the run continues single-model.

### Usage

```
/adversarial-review                          # auto: uncommitted changes, else branch diff vs default branch
/adversarial-review working-tree             # uncommitted changes only
/adversarial-review base develop             # branch diff vs merge-base with develop
/adversarial-review openspec/changes/foo/    # review documents as they stand
/adversarial-review fix iterations 2         # apply confirmed fixes, re-review, up to 2 rounds
/adversarial-review solo                     # skip Codex leg (cheaper)
/adversarial-review focus on the retry logic # free text becomes reviewer focus
```

Requires: Claude Code with the Workflow tool. Optional: [Codex CLI](https://github.com/openai/codex) (`codex login`) for the second model.

### Install

Via [skills.sh](https://skills.sh):

```
npx skills add igorsova/agentic-toolkit
```

Via Claude Code plugin marketplace:

```
/plugin marketplace add igorsova/agentic-toolkit
/plugin install agentic-toolkit@agentic-toolkit
```
