# Automatic local learning

Observe future Claude Code and Codex sessions, consolidate recurring procedures into skills, and propose changes that remove repeated manual work. For example, repeated Danger CI investigations can yield a diagnostics skill and a duration-monitoring proposal with evidence and an observable success condition.

## Installation

Requires macOS or Linux, Python 3.9+, SQLite with FTS5, and a current authenticated `codex` or `claude` CLI. Each source agent needs native command hooks. The runtime has no third-party Python dependencies.

From a persistent checkout:

~~~bash
python3 skills/self-learning/install.py
~~~

The installer merges owned hooks into `~/.claude/settings.json` and `~/.codex/hooks.json`, preserving unrelated settings and hooks. It symlinks the management skill into `~/.claude/skills/self-learning` and `~/.agents/skills/self-learning`. Hooks use a stable copy of the runtime in the state directory, so worktree cleanup cannot break background learning. Rerun the installer after runtime updates; keep the checkout for the management skill, or relink it after moving. Restart both hosts. Codex requires its normal initial hook-trust review and renewed review after hook-definition changes; the installer does not bypass it.

Installing the toolkit plugin alone does not register these user hooks. Run the installer once; do not also register duplicate project/plugin hooks. `--dry-run` previews destinations. `--home <directory> --state-dir <directory>` supports an isolated installation. Runtime paths are calculated during installation and are never committed as personal paths.

## Automatic flow

1. `Stop` and `SessionEnd` capture transcript coordinates. Snapshots deduplicate and pending turns coalesce. Hooks return without waiting for a model.
2. A detached worker reads bounded evidence and combines recent sessions from the same project, across both hosts. Worktrees sharing a local Git common directory share scope.
3. After two independent sessions contain user evidence, reflection can extract procedures and improvement proposals. The host validates all output before publication.
4. `UserPromptSubmit` injects active procedures matching meaningful task terms. Generic request words are ignored; startup without a task does not load an arbitrary recent procedure. Generated `SKILL.md` files live in one canonical project-scoped store; they are not installed globally for unrelated projects. `SessionStart` still resumes queued work and can surface health notices.
5. Relevant proposals surface once per content revision; unrelated prompts do not consume their notifications. The agent is instructed to discuss the suggestion and verify current capabilities before treating proposed infrastructure as available. Delivery does not prove that the user saw or accepted it.
6. Later explicit user results can reinforce or withdraw delivered guidance. Reported outcomes are included in subsequent reflection. Helpful proposals leave the pending queue; harmful skills stop appearing in context. Silence, loading a skill, and exit code zero do not establish usefulness.

Each skill/proposal needs exact quoted user evidence from two sessions. Skills also need tool-result evidence. A mismatched record ID can be repaired only when the quotation exactly matches one unique record in that same session; invented and ambiguous citations are rejected. Repeated polling in one session is not independent support. The model prefers updating existing generated slugs. Semantic equivalence and quality remain model judgments; the evidence gate does not prove causal improvement.

The worker can revise only its generated store. Changes to existing user/repository skills and installation of proposed monitors remain ordinary proposals for authorized follow-up.

## State and bounds

Default: `~/.local/share/agentic-learning/`, overridden by `AGENTIC_LEARNING_HOME` or `--state-dir`. A private SQLite database stores the queue, excerpts, artifacts, revisions, delivery receipts, outcomes and model-run receipts. Human-readable skills and proposals are derived views.

Edit `config.json` to configure:

| Setting | Default | Meaning |
|---|---|---|
| `enabled` | `true` | Capture, reflection and injection |
| `engine` | `auto` | `auto`, `claude` or `codex`; auto uses the triggering host |
| `model` | `null` | CLI default or an explicit model name |
| `codex_bin`, `claude_bin` | resolved at installation | Absolute CLI paths, including for GUI environments |
| `auto_skills` | `true` | Activate generated skills passing the evidence gate |
| `min_interval_seconds` | `900` | Minimum between model attempts per project |
| `max_calls_per_day` | `6` | Shared rolling 24-hour maximum, including failures |
| `timeout_seconds` | `180` | Model-process lifetime limit |
| `max_input_chars` | `32000` | Approximate evidence/artifact bundle bound |
| `max_sessions` | `12` | Recent independent sessions available for synthesis |

Claude additionally receives a $1 per-call CLI budget. Codex is bounded by calls, input and timeout, not an enforced monetary ceiling. Reflection uses the selected CLI's model provider and authentication; local state does not mean offline inference.

`AGENTIC_LEARNING_CODEX_BIN` and `AGENTIC_LEARNING_CLAUDE_BIN` select executable paths when GUI environments have a limited PATH.

There is no resident daemon or scheduled model polling. Hooks launch bounded workers; later source activity resumes retries and quota-deferred reflection. Queue state survives crashes. Live workers are not duplicated merely because a lease expires.

Optional administrative controls:

~~~bash
python3 skills/self-learning/learning.py status
python3 skills/self-learning/learning.py context --project . --prompt "Danger CI duration"
python3 skills/self-learning/learning.py disable
python3 skills/self-learning/learning.py enable
python3 skills/self-learning/learning.py feedback <artifact-id> --verdict harmful --note "Specific observed result"
python3 skills/self-learning/learning.py dismiss <proposal-id>
python3 skills/self-learning/install.py --uninstall
~~~

Disable stops new work; an already running reflection may finish. Human feedback is recorded as reported evidence. Model-extracted outcomes additionally need a user quotation strictly after the delivery snapshot in that source session. The last row already present at delivery cannot count as later feedback. Injected context explains that feedback review runs automatically after the turn, subject to the budget; the source assistant must not claim persistence before confirmation. Uninstall removes only owned hooks and matching symlinks, disables learning and preserves state and config backups.

## Read-only artifact discovery

```bash
python3 skills/self-learning/learning.py discover --project <checkout>
python3 skills/self-learning/learning.py discover --project <checkout> --source codex:<native-id> --source claude:<native-id>
python3 skills/self-learning/learning.py discover --project <checkout> --source codex:<native-id> --artifact <selected-artifact-id>
```

`--state-dir` precedes `discover` when overriding the store. Omit sources to list the project; multiple sources match any recorded relationship. An explicit `--artifact` includes that selection within the same project even without a source match. The JSON snapshot returns owner, database location, refresh time, artifact IDs/canonical paths, file availability, revision/status, evidence coordinates (including historical revisions), delivery receipts and reported outcomes. Supporting evidence, delivery and attributable outcomes carry distinct relationship labels. Missing source files remain unavailable references. Manual feedback appears on its artifact with a null source session unless native evidence recorded one.

This operation opens SQLite read-only without constructing `Store`, creating a missing store, running schema migrations, changing config/permissions, consuming proposal notifications, or recording deliveries/outcomes. It makes no model call and does not affect reflection budgets. A missing database returns `available: false`; an incompatible/corrupt database reports an error without repair. Ordinary reflection/recall work without planning metadata. SQLite manages its normal reader coordination when the database uses WAL.

The planning skill can query this interface on foreground continuation/delivery and keep compact timestamped links. Its entry owns grouping/title; this runtime keeps artifact authority and never writes that entry. An entry snapshot is navigation, not live inventory or evidence of use. Explicit feedback still targets `feedback <artifact-id>`; gates and automatic outcome rules above are unchanged. See the [session contract](../skills/planning/records.md) and [isolated pilot](session-artifacts.md).

For runtime updates, verify an isolated `install.py --home <temporary-home> --state-dir <temporary-state>` before an authorized live reinstall. The management-skill symlink alone cannot update deployed Python copies. Installation continues to preserve existing symlink targets and unrelated hooks; switching a live management symlink to another checkout is a separate rollout action.

## Data and execution boundaries

The installer does not backfill old sessions. Selected user/assistant text, tool calls and results become private excerpts with source-path/row provenance. System/developer messages, thinking and images are excluded. Common credentials are redacted; this is not a complete secret detector. Excerpts persist until the state directory is removed; completed queue coordinates are pruned after 30 days. Do not commit this directory.

The model receives selected excerpts as untrusted evidence. Headless children use disposable working directories, recursion suppression, disabled hooks/customizations, tool restrictions, structured output and timeouts. The host checks scope, slugs, quotes and independence before writing generated artifacts. These controls do not prove semantic correctness.

## Open-source reuse

`skills/self-learning/upstream_queue.py` is an unchanged copy of [Self-Improving Skills' queue](https://github.com/UniM0cha/self-improving-skills/blob/62d15b60d0442ba7777eaf82f9f2050e87c18e85/plugins/chatgpt-codex-self-improving-skills/scripts/review_queue.py).

- Commit: `62d15b60d0442ba7777eaf82f9f2050e87c18e85`.
- Git blob: `23e7048d6911a31de9e638b6af4be6545928ea87`.
- MIT license; full original notice in `skills/self-learning/UPSTREAM_LICENSE`.

The integration uses its queue APIs and connection factory with an explicit shared database path; its default Codex-directory discovery is unused. Project evidence, scoped publication, output validation, independent-session proposals and cross-host recall are the toolkit's integration.

The detached hook/worker pattern follows the same project's [Claude analyzer](https://github.com/UniM0cha/self-improving-skills/blob/62d15b60d0442ba7777eaf82f9f2050e87c18e85/plugins/claude-code-self-improving-skills/scripts/analyze_turn.py). Canonical scoped guidance and separate learning/publication decisions were informed by [Shadowclone's design](https://github.com/theonly1me/shadowclone/blob/ab263630a82c640a9c3250fbce49a24402a946a9/docs/design/017-self-improving-agent-environment.md); no Shadowclone code is vendored.

Host contracts: [Codex hooks](https://learn.chatgpt.com/docs/hooks), [Claude hooks](https://code.claude.com/docs/en/hooks), [Claude headless execution](https://code.claude.com/docs/en/headless).

## Verification

~~~bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests -p 'test_self_learning.py' -v
~~~

The original 19 learning tests use temporary state and synthetic CI conversations. They cover both transcript formats, snapshot cutoffs, long-trace intent, credential redaction, concurrent capture, worker exclusivity, single-session rejection, cross-host learning/recall, relevant proposal notification, exact-quote validation, scope, strictly later harmful feedback, quota, installation preservation/removal and a fake executable speaking the real runner protocol.

The additional session/discovery suite (`python3 -B -m unittest discover -s tests -p 'test_session_artifacts.py' -v`) verifies session identity, concurrency, legacy compatibility, provenance relationships, read-only listing and isolated deployment. These tests verify integration invariants, not improved real-world task performance.

The opt-in [native end-to-end evaluation](self-learning-evaluation.md) uses actual host sessions, hooks, detached workers and both authenticated reflection engines. It includes output review, application to a held-out run, negative-feedback withdrawal and abstention on noisy injected evidence. It uses synthetic project data and isolated learning state; it can incur provider usage. Run each command with a new, empty output directory:

~~~bash
python3 -B tests/e2e_self_learning.py --live --output /private/tmp/learning-native-evaluation
python3 -B tests/e2e_self_learning.py --live --negative-only --output /private/tmp/learning-negative-evaluation
~~~

The native harness shares Codex file authentication by symlink without reading or copying credentials. Claude uses normal authentication with only the isolated hook settings enabled. It vets its own hook definitions and uses Codex's invocation-only hook-trust bypass for this controlled test; this does not approve production hooks. Native Claude transcripts remain in Claude's normal session directory. Private reports contain local paths and session identifiers and must not be committed. Assertions and saved answers support human review; they are not a general semantic quality oracle.

The generic skill validator could not start in the available Python runtimes because PyYAML was absent. Repository-required frontmatter (including `argument-hint`) was instead parsed and checked with Ruby's YAML parser; runtime Python remains dependency-free.
