# agentic-toolkit

Personal agent toolkit. See [ARCHITECTURE.md](ARCHITECTURE.md) for how the pipelines work and [CHANGELOG.md](CHANGELOG.md) for history. Three skills:

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
/adversarial-review                            # auto: uncommitted changes, else branch diff vs default branch
/adversarial-review working-tree               # uncommitted changes only
/adversarial-review --base develop             # branch diff vs merge-base with develop
/adversarial-review openspec/changes/foo/      # review documents as they stand
/adversarial-review --fix --iterations 2       # apply confirmed fixes, re-review, up to 2 rounds
/adversarial-review --strict                   # low-noise: only merge-blocking findings
/adversarial-review --no-codex                 # skip Codex leg (cheaper single-model)
/adversarial-review --effort low               # cheap precision pass: merge-blocking findings only
/adversarial-review --effort max               # widest net, strongest reasoning, 3-vote panel
/adversarial-review --cwd ~/src/other-repo     # review a checkout outside the cwd
/adversarial-review focus on the retry logic   # free text becomes reviewer focus
```

Requires: Claude Code with the Workflow tool. Optional: [Codex CLI](https://github.com/openai/codex) (`codex login`) for the second model.

## crucible

End-to-end build pipeline named after the vessel ore is tested in under fire: an idea goes in, gets its assumptions attacked by a skeptic panel, survives a debate with you, becomes a judged plan, then tested code. Budget-scaled at every fan-out.

```
Recon → [skeptic panel ∥] → consolidate → ══ debate gate ══
      → [competing plans ∥] → plan judge → ══ plan gate ══
      → sequential develop → test suite + fix loop → hostile review → refute votes → fix
```

- Skeptics attack every assumption with file evidence (feasibility / necessity / scope / adversary lenses); you rule on the survivors — rulings are settled, never re-litigated.
- Plans compete (minimal vs robust vs refactor-first); a judge file-verifies their claims and synthesizes one, test-first when test infra exists.
- Implementation is sequential with per-task test evidence; a fresh hostile reviewer plus a 2-vote refute panel gate the result.
- Works without the Workflow tool too: [PLAYBOOK.md](skills/crucible/PLAYBOOK.md) is the same pipeline as a sequential protocol for Codex CLI or any Agent-Skills-compatible agent.

### Usage

```
/crucible add rate limiting to the public API      # gated run: debate → plan gate → build → test
/crucible --auto migrate configs to TOML           # one-shot; halts instead of guessing when a ruling is needed
/crucible --effort low ...                         # cheap pass: 2 skeptics, 2 planners, no refute panel
/crucible --effort high ...                        # wide net: 4 skeptics, 3 planners, 3 fix rounds
/crucible --phase test                             # re-run a single phase
/crucible --cwd ~/src/other-repo ...               # build in a checkout outside the cwd
```

Requires: Claude Code with the Workflow tool for the orchestrated path; anything that can read/edit files and run shell commands for the playbook path.

## session-migration

Claude Code Desktop stores session records per account, so switching accounts hides every session created under the old one — gone from the sidebar, from `list_sessions`, from `search_session_transcripts`. This skill finds them again and puts a chosen one back in front of you. macOS only.

It also fires implicitly: when a session search comes up empty, check the other accounts before telling the user the conversation does not exist. Names are matched fuzzily, so a half-remembered or misspelled title is enough.

Two ways into the sidebar, with different costs:

| | `import` | `move` |
|---|---|---|
| Mechanism | `claude://resume?session=…` deep link → the app's own CLI-session import | relocates the record file between account directories |
| Appears | immediately | after a full app restart |
| Loses | title, model, original timestamps | nothing |

A third surface is separate: past *desktop* sessions have no background-job entry, so they never show in the CLI `claude agents` view under any account. `job` synthesizes one.

### Usage

```
/session-migration                              # list what is hiding in other accounts
/session-migration astro theme                  # fuzzy-find it across accounts
/session-migration the one about metro ports    # --search-transcripts when only content is remembered
/session-migration <name> --import              # live import into the current account
/session-migration <name> --move                # relocate the record, full fidelity, needs a restart
```

Requires: Python 3, macOS, Claude Code Desktop.

## Install

Via [skills.sh](https://skills.sh):

```
npx skills add hardworker/agentic-toolkit
```

Via Claude Code plugin marketplace:

```
/plugin marketplace add hardworker/agentic-toolkit
/plugin install agentic-toolkit@agentic-toolkit
```

For Codex CLI, copy or symlink the skill directories into `.agents/skills/` — crucible runs its playbook path there.
