# agentic-toolkit — Architecture

Two debate pipelines, two utility skills. The pipelines share one goal: output you don't have to re-check, because every claim was attacked before it reached you, at a cost every fan-out caps. Both are pure prose — a SKILL.md that spawns its own agents, no orchestrator script.

| Skill | Does | Agents |
|---|---|---|
| [adversarial-review](#adversarial-review) | cross-model debate review of finished work — diff, working tree, or documents | 4 + 2 Codex calls |
| [crucible](#crucible) | idea → grill → attacked assumptions → plan → code → verify | 6–12, capped |
| [session-migration](#session-migration) | find any past session, route it to the surface you want | none |
| [cf-access](#cf-access) | keep CLI tools, Node clients and MCP servers authenticated to Cloudflare Access | none |

## adversarial-review

Two independent reviewers (Claude, Codex) review the same target, argue until they agree or deadlock, then a judge re-verifies the survivors in the files.

```
             ┌────────────┐
             │   Scope    │    cheap agent: file list, summary, diff command
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

### Structure

- The main thread orchestrates only: it owns whose finding is whose and what is still disputed, and never reads the target or takes a side.
- Every stage returns JSON against a shape stated in its prompt — one contract for both legs.
- Prompts carry a file list and a diff command, never the diff, so the same review works on 3 files or 66.
- The Codex leg is `codex exec --sandbox read-only --output-schema … -o answer.json`; its reasoning transcript stays out of the orchestrator context, and its answer passes through verbatim.

### Decisions

- **A plain skill, not an orchestrator script.** Nothing here needs deterministic control flow: gates are conversations, loops are bounded by stated counts. The cost is that loop guards are instructions rather than code.
- **Scope is an agent, though it is only git.** Inline, the diff lands in the one context that must survive the whole run, and "never review the target" decays from a boundary into an instruction.
- **Findings carry an evidence requirement.** A `defect` needs a concrete failure scenario; a `design` finding needs a concrete better alternative. Severity anchors on merge impact.
- **Round 1 cross-examines against the files.** Plausibility judgments are banned. This is the hallucination filter.
- **Later rounds allow two moves:** concede citing evidence, or defend with evidence not already given. Deferring is not a resolution; repetition is a deadlock. Without those rules a debate converges on whoever argues hardest ([consensus cost](https://arxiv.org/html/2605.00914v1), [debate or vote](https://arxiv.org/abs/2508.17536)).
- **Judge verification is tiered.** Highs get opened; an uncorroborated high must survive a refutation attempt; lows ride on the record, where a miss costs least.
- **Independent agreement outranks agreement reached mid-debate.** The judge treats the latter as one reviewer's finding that survived an argument.
- **The fix loop has three guards:** a mutation guard (touching a file no finding names halts the run), anti-anchoring memory, and a stagnation fingerprint.
- **A missing Codex degrades, never aborts.** A fresh Claude critic stands in, so nothing reaches the judge uncontested.
- **One depth knob.** `--effort` shares its axis with `/code-review`: low buys precision, high buys coverage.

### Result contract

Prose to the user, plus one temp file at the end of the run:

```jsonc
{
  "status": "clean | issues-found | stagnant | max-iterations | scope-violation | nothing-to-review | error",
  "target": "origin/main", "iterations": 1, "rounds": 2, "effort": "medium", "codexAvailable": true,
  "confirmed": [ { "id", "kind", "file", "line", "severity", "title", "description",
                   "agreement", "settled", "fixRecommendation" } ],
  "rejected":  [ { "id", "reason" } ],
  "conceded":  [ { "id", "title" } ],
  "fixed":     [ "issue ids (fix mode)" ],
  "summary":   "judge's narrative verdict"
}
```

## crucible

Where adversarial-review challenges finished work, crucible challenges work before it exists — the user, then the assumptions, then the plan, then the diff — so bad premises die at the cheapest point.

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

### Structure

- No orchestrator. The main loop runs the phases, holds the gates, and spawns isolated agents only where isolation *is* the mechanism: recon, each lens, the defender, each review round.
- State is four files, in the session scratchpad or `~/.crucible/<repo>/<timestamp>/` — never the working tree the reviewer inspects:

```
brief.md       goal · non-goals · assumptions (id | claim | source) · unknowns
               · constraints · acceptance criteria · settled rulings
challenges.md  verdict per assumption · surviving challenges · open questions
plan.md        ≤8 tasks (id | files | steps | acceptance | test plan | dependsOn)
progress.md    per task: files changed, test evidence, deviations · verify rounds
```

- `--auto` is the no-human mode: no grill, no gates, and a halt (`challenged`) wherever a ruling is needed, never a guess.

### Decisions

- **Debate for critique, refutation for verification, never for accuracy ensembling.** Budget-matched studies favour cheap self-consistency, and most measured debate gains are just voting ([token economies](https://arxiv.org/abs/2406.06461), [debate or vote](https://arxiv.org/abs/2508.17536)). So adversarial agents appear only where dissent is the product.
- **Grill before spending a token.** The panel can only attack claims the brief contains, so a vague brief buys attacks on nothing.
- **Recon is delegated; everything downstream is not.** It is the largest read of the run and its output is one page. The main loop then argues the gate on file-cited challenges, opening only the files a ruling turns on.
- **A defender sits between panel and user.** Skeptics are paid to attack, so some attacks are wrong; without a refuter the user becomes one. Product calls (`needs-user`) are exempt however well argued.
- **Skeptics are isolated and see unattributed assumptions.** Cross-conditioning collapses diversity ([consensus cost](https://arxiv.org/html/2605.00914v1)), and marking a claim as the user's measurably raises agreement with it ([SycEval](https://arxiv.org/abs/2502.08177)).
- **Each skeptic's prompt defines success as effective critique.** Self-critique degenerates once a model is confident ([degeneration-of-thought](https://arxiv.org/abs/2305.19118)); uncertainty maps to `shaky`, never `holds`.
- **Best-of-N plans with a verifying judge.** Candidate generation plus independent selection is the one multi-model pattern with consistent coding wins ([SWE-bench analysis](https://arxiv.org/abs/2506.17208)). A plan naming wrong files is worse than no plan, so the judge opens them.
- **Sequential develop, no parallel implementers.** Parallel workers make conflicting implicit decisions, and most multi-agent failures are coordination failures ([MAST](https://arxiv.org/abs/2503.13657)). Blocked tasks stop the run.
- **Fresh-context hostile review, looped to convergence.** Models favour their own output ([self-preference](https://arxiv.org/abs/2404.13076)), so reviewers see only the diff and the plan. One shot was the old weakness: a fix introduces its own defects.
- **The verify loop is a [Ralph loop](https://ghuntley.com/ralph/) — its state is a file, not memory.** Each pass reads `progress.md`, appends its round record *before* judging anything, then checks three named exits (`clean`, `capped`, `stagnant`). A compacted context resumes mid-loop instead of mistaking round 1 for a finished job.
- **Simplification is a review angle, not a phase.** Everything upstream pushes toward addition, and nothing else in the pipeline ever removes a line. It runs as its own agent — one reviewer holding both mandates dilutes into neither — at two altitudes: surface waste, and over-built structure walked down a YAGNI ladder. Every finding must name the concrete smaller shape.
- **Test-first ordering, hollow-test hunting.** Agents left alone write tests that assert whatever the code does.
- **Caps, not a budget object.** ≤10 assumptions, ≤8 tasks, ≤6 findings per round, one page per artifact. Multi-agent runs cost ~15× chat, so every fan-out is a fixed small number.
- **Overhead must be earned.** The skill's first rule is when *not* to run it: a one-sentence uncontested change gets built directly.

### Portability

Written to the [Agent Skills standard](https://agentskills.io/specification): no tool names, and a single-loop fallback wherever a fresh agent would be used.

The fallback is worded as a spawn that is *absent or failed*, never as a capability question. Phrased as permission, a host whose own prompt discourages subagents takes it — and the skeptic panel then runs inside the context it exists to be independent of. So invoking crucible **is** the user asking, and the report names any phase that fell back.

Validation is field runs only.

## session-migration

No subagents, no debate. Two mechanisms hide past work: desktop session records are scoped per account, so an account switch strands everything before it, and terminal sessions get no desktop record at all. Both are invisible to the sidebar and to `list_sessions`.

```
~/Library/Application Support/Claude/claude-code-sessions/<accountId>/<orgId>/local_<uuid>.json   ← account-scoped record
~/.claude/projects/<slug(cwd)>/<cliSessionId>.jsonl                                               ← transcript, account-agnostic
~/.claude/jobs/<first-8-of-cliSessionId>/{state.json,timeline.jsonl}                              ← CLI `claude agents` registry
```

The transcript is the durable artifact; the other two stores are pointers to it. So most of what looks like migration is writing the missing pointer:

| Destination | Route | Cost |
|---|---|---|
| desktop sidebar, now | `import` — the `claude://resume` deep link | new record id, metadata reset |
| desktop sidebar, intact | `move` — relocate the record | full app restart |
| terminal | `resume` — print `claude --resume` | none; the transcript was always reachable |
| `claude agents` | `job` — synthesize the registry entry | none |

### Decisions

- **Three app behaviours drive the rest.** Records live in an in-memory map rebuilt only on launch or account switch, so a copied file stays invisible until restart. The deep link builds a fresh record from the transcript *in the current account* — the only path avoiding one. And the app's own recovery scan skips any transcript held under *any* account, so a stranded session must be reached deliberately.
- **`import` and `move` are mutually exclusive.** They produce different record ids, so running both puts one conversation in the sidebar twice. Each refuses when the other has run.
- **A live background agent blocks every `claude --resume` route.** The claim is a socket, not a status: a job reading `done` can still hold it, and no UI shows it. All routes preflight it and name the holding pids; `--force` is deliberately powerless, because the refusal comes from the CLI.
- **Fuzzy by default.** The trigger case is a half-remembered name. Ambiguity is surfaced, never guessed — two close candidates print and stop.
- **The CLI is always searched.** Scoping to desktop records skipped ~90% of sessions on a real machine.
- **Nothing is destroyed.** `move` renames, `--copy` duplicates, an existing destination is refused. The one removal is a tombstone under `--force`.
- **Never patch a loaded record** — the in-memory copy wins and overwrites disk, so renames go through the app's own API.
- **Verify before reporting**, the one habit shared with the debate skills.

### Result contract

Plain stdout, not JSON: the consumer is the agent's own reading. Every mutation prints source path, destination path and the refresh the user must perform. `--dry-run` on every mutating subcommand prints that report and writes nothing.

## cf-access

The only skill that installs a background process.

An Access app with an IdP-only policy has no service-token path. Its JWT comes from a browser SSO round-trip and lasts about a day. So any client that reads its credential once at startup works for a day, then fails with a login redirect. Three layers, chosen by how much the client can change.

```
cf-access              broker: mint / cache / renew, one place that knows how
   ↑ per invocation                    ↑ per request
shell, curl, MCP launchers      cf-access-proxy ── 127.0.0.1:8780 (dynamic, header names upstream)
                                        │      └─ 127.0.0.1:<port> (fixed route, any language)
                                        ↑
                           cf-access-preload.cjs (NODE_OPTIONS=--require, patches http/https/fetch)
```

### Decisions

- **A broker, not per-client auth.** Every client gets a token or a URL. Nothing else knows `cloudflared` exists, so a newly gated tool is a config line.
- **Origins, never paths.** `cloudflared` caches per hostname, so a path misses the cache and re-mints forever.
- **`login` clears the cache first**, or `cloudflared` returns the cached token and the refresh is a no-op. The old token is stashed and restored on failure.
- **Cache files are found by the token's `aud`.** A hostname glob misses apps under a wildcard policy.
- **Gating is learned, not configured.** The first request to an origin goes out bare; only a login redirect proves a token is needed.
- **A credential on the request wins, unless Access rejects it.** The broker steps in only on rejection, so working auth is never swapped for a login the client cannot perform.
- **The login deadline lives in the broker**, where every caller routes through. It settles the mint rather than waiting for the child to die: `cloudflared` ignores `SIGTERM` and holds its pipe open.
- **A bounded hold, not an unbounded wait.** A request waits, then gets `511` while the login continues; the retry finds a token, so a human tap never races a client timeout.
- **The allowlist is domain suffixes, and it is the security boundary.** Without it the loopback port is an open forwarder. No file means allow nothing. One implementation serves proxy and preload, because two would drift into either half of the failure. Re-read on a short TTL, not watched — a watcher in the preload would stop every Node process exiting.
- **Single-flight minting with a login cooldown.** A stampede collapses into one mint per origin; the cooldown stops a burst of failures stacking up browser tabs.
- **A browser window names its cause.** Every SSO path crosses one funnel, so the trace is emitted there. It fires before the attempt, since a line that waited for the mint would arrive after the window it explains. Single-flight keeps it honest — only the request that starts a mint is named.
- **A caller with no trace supplies its own.** Direct mode is the case that most needs explaining — a window from a shell or an agent's Bash call is the one nobody can account for later — so the broker names and logs itself. Only a login typed at a terminal skips the page: a tty proves someone knows who asked.
- **Where no client can identify itself, the route does.** A fixed-port client sits on loopback and knows nothing about cf-access, and the preload must not divert `127.0.0.1`. So a label on its config line becomes that traffic's name.
- **The explanation is in the window too, and cannot be an iframe.** The IdP refuses framing, and a frame would partition the org session cookie. So a proxy-opened login lands on a local page that links out.
- **The client names itself.** The preload knows its own process; the proxy could only guess from a socket. Identity and session are separate headers, so no layer parses another's text.
- **Ids on the wire, names at the edge.** The preload must cost nothing, so reading session records is the page generator's job. It degrades in steps — title, worktree, directory — since a title lands only after the first turn and a terminal session has no desktop record at all.
- **What reaches the log is an allowlist.** Process ids, script name, session id, request path without its query. Never argv, environment values or headers — all three carry credentials. Wire values are quoted and bounded.
- **Our own headers never leave the proxy.** The whole namespace is stripped, so the next one is covered before it exists.
- **Bodies are buffered** so a token retry replays a POST byte-for-byte. **The preload never patches the proxy**, which would aim it at its own port.
- **Config is polled, and a bad config never exits.** Editors replace files, breaking an inode watcher; under launchd, exiting is a restart loop.
- **The plist carries the daemon's whole environment.** launchd starts bare. A knob the installer does not carry is one the daemon cannot see.

### Result contract

Status codes and one log line per event, not JSON — the consumers are ordinary clients. The proxy originates `511` (no token), `403` (host not allowed), `508` (upstream is the proxy), `400` (missing upstream header, also the health check) and `502` (transport).

`install.sh status` is the single diagnostic, because "no token", "daemon down", "host not allowed" and "not installed" look identical from the client side.

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

Installed two ways, both scanning for `SKILL.md`: `npx skills add hardworker/agentic-toolkit` or `/plugin marketplace add hardworker/agentic-toolkit`.

Locally the installs are symlinks into this repo (`~/.claude/skills/<name>`, `~/.agents/skills/<name>`), so edits go live with no update step — don't run `npx skills update` over them.

cf-access also installs *outside* the skill: `install.sh` symlinks its scripts into a bin dir and loads a launchd agent, so the skill dir stays the source of truth while the daemon runs from a stable path.
