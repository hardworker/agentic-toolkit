export const meta = {
  // a crucible is the vessel ore is tested in under fire: an idea goes in,
  // its assumptions get attacked, tested code comes out
  name: 'crucible',
  description: 'End-to-end feature pipeline: recon, challenge the assumptions, plan, develop, test — budget-scaled',
  whenToUse: 'Take a rough idea to tested code with the assumptions debated instead of rubber-stamped. Phase-parameterized: surface / plan / develop / test run as separate invocations with user gates between, or full for one-shot.',
  phases: [
    { title: 'Recon', detail: 'map the repo, distill the idea into a brief with explicit assumptions' },
    { title: 'Surface', detail: 'skeptic panel attacks every assumption; consolidator verifies contested verdicts in the files' },
    { title: 'Plan', detail: 'competing plans from different angles; judge synthesizes one, verifying file claims' },
    { title: 'Develop', detail: 'sequential task implementation with per-task test evidence' },
    { title: 'Test', detail: 'full suite + bounded fix loop' },
    { title: 'Review', detail: 'fresh-eyes hostile review of the produced change; refute votes on highs' },
    { title: 'Fix', detail: 'apply confirmed findings, re-run suite once' },
  ],
}

// ---------- args ----------
const ARGS = (() => {
  if (typeof args !== 'string') return args || {}
  try { return JSON.parse(args) || {} } catch { return {} }
})()
const runPhase = ARGS.phase || 'full'          // surface | plan | develop | test | full
const idea = ARGS.idea || ''                    // free-text feature idea (surface/full)
const userAssumptions = Array.isArray(ARGS.assumptions) ? ARGS.assumptions : []
const focus = ARGS.focus || ''
const cwd = ARGS.cwd || null                    // working directory: absolute repo root when not the session cwd
const git = cwd ? `git -C ${cwd}` : 'git'
const repoNote = cwd ? `\nRepository root: ${cwd} — file paths are relative to it; run every git command as \`${git} ...\` and Read/Edit files under that root.` : ''
// ---------- effort ----------
// depth presets, same scale as adversarial-review and /code-review: low/medium buy
// precision, high and above buy coverage. agentEffort null = inherit the session tier.
// medium = the 1.0 pipeline unchanged. legacy --thorough maps to high.
const EFFORT = {
  low:    { skeptics: 2, planners: 2, fixRounds: 1, refuteVotes: 0, agentEffort: 'low',   judgeEffort: 'medium' },
  medium: { skeptics: 3, planners: 2, fixRounds: 2, refuteVotes: 2, agentEffort: null,    judgeEffort: 'high' },
  high:   { skeptics: 4, planners: 3, fixRounds: 3, refuteVotes: 2, agentEffort: 'high',  judgeEffort: 'high' },
  xhigh:  { skeptics: 4, planners: 3, fixRounds: 3, refuteVotes: 3, agentEffort: 'xhigh', judgeEffort: 'xhigh' },
  max:    { skeptics: 4, planners: 3, fixRounds: 3, refuteVotes: 3, agentEffort: 'max',   judgeEffort: 'max' },
}
const effortLevel = Object.hasOwn(EFFORT, ARGS.effort) ? ARGS.effort : (ARGS.thorough ? 'high' : 'medium')
const E = EFFORT[effortLevel]
const eff = (tier) => (tier ? { effort: tier } : {})
// threaded between phase invocations (main thread passes prior results back in)
let repoMap = ARGS.repoMap || null
let brief = ARGS.brief || null
const resolutions = Array.isArray(ARGS.resolutions) ? ARGS.resolutions : []
let plan = ARGS.plan || null

// ---------- budget ----------
// rough per-subagent cost observed in this repo's field tests: ~50–80k output tokens
const PER_AGENT = 70_000
function scaledCount(want, label) {
  if (!budget.total) return want
  // reserve half the remaining budget for the phases after this fan-out
  const affordable = Math.floor(budget.remaining() / (PER_AGENT * 2))
  const n = Math.max(2, Math.min(want, affordable))
  if (n < want) log(`budget tight: ${n} ${label} instead of ${want}`)
  return n
}
function budgetExhausted(phaseName) {
  if (budget.total && budget.remaining() < PER_AGENT * 2) {
    log(`budget exhausted before ${phaseName} (${Math.round(budget.remaining() / 1000)}k left)`)
    return true
  }
  return false
}
const spentAt = { start: budget.spent() }

// ---------- schemas ----------
const RECON_SCHEMA = {
  type: 'object',
  properties: {
    repoMap: {
      type: 'object',
      properties: {
        summary: { type: 'string', description: 'one paragraph: what this repo is and where the idea lands in it' },
        keyFiles: { type: 'array', items: { type: 'string' }, description: 'files the work will touch or must imitate' },
        conventions: { type: 'string', description: 'patterns the change must follow (max 3 sentences)' },
        testCommand: { type: 'string', description: 'exact command to run the relevant test suite; empty string if none exists' },
        lintCommand: { type: 'string', description: 'exact lint/typecheck command; empty string if none' },
      },
      required: ['summary', 'keyFiles', 'conventions', 'testCommand', 'lintCommand'],
    },
    brief: {
      type: 'object',
      properties: {
        goal: { type: 'string', description: 'one sentence: the outcome the user wants' },
        nonGoals: { type: 'array', items: { type: 'string' } },
        assumptions: {
          type: 'array',
          items: {
            type: 'object',
            properties: {
              id: { type: 'string', description: 'a-1, a-2, ...' },
              text: { type: 'string' },
              source: { type: 'string', enum: ['user', 'inferred'], description: 'user = stated by the user; inferred = implicit in the idea' },
            },
            required: ['id', 'text', 'source'],
          },
        },
        unknowns: { type: 'array', items: { type: 'string' } },
        constraints: { type: 'array', items: { type: 'string' } },
        acceptanceCriteria: { type: 'array', items: { type: 'string' }, description: 'observable checks that would prove the goal is met' },
      },
      required: ['goal', 'nonGoals', 'assumptions', 'unknowns', 'constraints', 'acceptanceCriteria'],
    },
  },
  required: ['repoMap', 'brief'],
}

const VERDICT_PROPS = {
  assumptionId: { type: 'string' },
  verdict: { type: 'string', enum: ['holds', 'shaky', 'wrong'] },
  evidence: { type: 'string', description: 'file:line or concrete reasoning; max 2 sentences' },
  counterproposal: { type: 'string', description: 'what to do instead, when verdict is shaky/wrong' },
}
const SKEPTIC_SCHEMA = {
  type: 'object',
  properties: {
    verdicts: { type: 'array', items: { type: 'object', properties: VERDICT_PROPS, required: ['assumptionId', 'verdict', 'evidence'] } },
    extraRisks: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          title: { type: 'string' },
          severity: { type: 'string', enum: ['high', 'medium', 'low'] },
          detail: { type: 'string', description: 'max 2 sentences' },
        },
        required: ['title', 'severity', 'detail'],
      },
    },
    questionsForUser: { type: 'array', items: { type: 'string' } },
    summary: { type: 'string' },
  },
  required: ['verdicts', 'extraRisks', 'questionsForUser', 'summary'],
}

const CONSOLIDATED_SCHEMA = {
  type: 'object',
  properties: {
    assumptionVerdicts: { type: 'array', items: { type: 'object', properties: VERDICT_PROPS, required: ['assumptionId', 'verdict', 'evidence'] } },
    challenges: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          id: { type: 'string', description: 'c-1, c-2, ...' },
          severity: { type: 'string', enum: ['high', 'medium', 'low'] },
          assumptionId: { type: 'string', description: 'the assumption this attacks, when applicable' },
          title: { type: 'string' },
          evidence: { type: 'string', description: 'max 2 sentences, cite file:line where possible' },
          counterproposal: { type: 'string', description: 'the concrete alternative' },
          recommendation: { type: 'string', enum: ['keep-original', 'adopt-counterproposal', 'needs-user'] },
        },
        required: ['id', 'severity', 'title', 'evidence', 'counterproposal', 'recommendation'],
      },
    },
    openQuestions: { type: 'array', items: { type: 'string' } },
    proceed: { type: 'string', enum: ['proceed', 'debate', 'halt'], description: 'proceed = nothing fundamental; debate = the user must rule on the challenges; halt = the idea is contradicted by evidence' },
    summary: { type: 'string' },
  },
  required: ['assumptionVerdicts', 'challenges', 'openQuestions', 'proceed', 'summary'],
}

const TASK_PROPS = {
  id: { type: 'string', description: 't-1, t-2, ...' },
  title: { type: 'string' },
  intent: { type: 'string', description: 'what this task achieves, max 2 sentences' },
  files: { type: 'array', items: { type: 'string' }, description: 'files this task creates or edits' },
  steps: { type: 'string', description: 'how, max 3 sentences' },
  acceptance: { type: 'string', description: 'observable check that the task is done' },
  testPlan: { type: 'string', description: 'which tests to add/run for this task; empty if none' },
  dependsOn: { type: 'array', items: { type: 'string' } },
}
const TASK = { type: 'object', properties: TASK_PROPS, required: ['id', 'title', 'intent', 'files', 'steps', 'acceptance', 'testPlan', 'dependsOn'] }

const PLAN_DRAFT_SCHEMA = {
  type: 'object',
  properties: {
    angle: { type: 'string' },
    tasks: { type: 'array', items: TASK },
    testStrategy: { type: 'string', description: 'max 3 sentences' },
    risks: { type: 'array', items: { type: 'string' } },
    tradeoffs: { type: 'string', description: 'what this plan sacrifices, max 2 sentences' },
  },
  required: ['angle', 'tasks', 'testStrategy', 'risks', 'tradeoffs'],
}

const FINAL_PLAN_SCHEMA = {
  type: 'object',
  properties: {
    goal: { type: 'string' },
    tasks: { type: 'array', items: TASK },
    testStrategy: { type: 'string' },
    risks: { type: 'array', items: { type: 'string' } },
    planChallenges: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          title: { type: 'string' },
          detail: { type: 'string', description: 'max 2 sentences' },
          recommendation: { type: 'string' },
        },
        required: ['title', 'detail', 'recommendation'],
      },
      description: 'decisions the user should still rule on; empty when none',
    },
    rationale: { type: 'string', description: 'which draft won, what was grafted from the others, why; max 3 sentences' },
  },
  required: ['goal', 'tasks', 'testStrategy', 'risks', 'planChallenges', 'rationale'],
}

const TASK_RESULT_SCHEMA = {
  type: 'object',
  properties: {
    status: { type: 'string', enum: ['done', 'blocked'] },
    changedFiles: { type: 'array', items: { type: 'string' }, description: 'every file modified/created, exactly as git status reports it' },
    summary: { type: 'string', description: 'what was done, max 2 sentences' },
    testEvidence: { type: 'string', description: 'test command run and its outcome; empty if no tests apply' },
    deviations: { type: 'array', items: { type: 'string' }, description: 'each departure from the task spec and why' },
    blockedReason: { type: 'string' },
  },
  required: ['status', 'changedFiles', 'summary', 'testEvidence', 'deviations'],
}

const SUITE_SCHEMA = {
  type: 'object',
  properties: {
    ran: { type: 'boolean' },
    command: { type: 'string' },
    pass: { type: 'boolean' },
    failures: {
      type: 'array',
      items: {
        type: 'object',
        properties: { test: { type: 'string' }, error: { type: 'string', description: 'shortest decisive line' } },
        required: ['test', 'error'],
      },
    },
    notes: { type: 'string' },
  },
  required: ['ran', 'command', 'pass', 'failures'],
}

const FINDING_PROPS = {
  id: { type: 'string' },
  kind: { type: 'string', enum: ['defect', 'design'] },
  file: { type: 'string' },
  line: { type: 'integer' },
  severity: { type: 'string', enum: ['high', 'medium', 'low'] },
  title: { type: 'string' },
  description: { type: 'string', description: 'defect: concrete failure scenario. design: the materially better alternative. Max 3 sentences' },
  impact: { type: 'string', description: 'blast radius in one sentence' },
  fixRecommendation: { type: 'string' },
}
const REVIEW_SCHEMA = {
  type: 'object',
  properties: {
    findings: { type: 'array', items: { type: 'object', properties: FINDING_PROPS, required: ['id', 'kind', 'file', 'severity', 'title', 'description', 'impact', 'fixRecommendation'] } },
    summary: { type: 'string' },
    exitSignal: { type: 'boolean', description: 'true only when nothing merge-blocking remains' },
  },
  required: ['findings', 'summary', 'exitSignal'],
}

const REFUTE_SCHEMA = {
  type: 'object',
  properties: {
    refuted: { type: 'boolean' },
    reasoning: { type: 'string', description: 'max 2 sentences, cite file:line' },
  },
  required: ['refuted', 'reasoning'],
}

const FIXUP_SCHEMA = {
  type: 'object',
  properties: {
    fixed: { type: 'array', items: { type: 'string' } },
    skipped: {
      type: 'array',
      items: {
        type: 'object',
        properties: { id: { type: 'string' }, reason: { type: 'string' } },
        required: ['id', 'reason'],
      },
    },
    changedFiles: { type: 'array', items: { type: 'string' } },
    notes: { type: 'string' },
  },
  required: ['fixed', 'skipped', 'changedFiles'],
}

// ---------- prompts ----------
function reconPrompt() {
  return `You are the recon agent of an end-to-end build pipeline. Map the repository and distill the idea into a brief. Do NOT plan or implement anything.${repoNote}

Idea (verbatim from the user):
${idea}
${userAssumptions.length ? `\nAssumptions the user stated (keep verbatim, source "user"):\n${userAssumptions.map((a) => `- ${a}`).join('\n')}` : ''}${focus ? `\nExtra focus: ${focus}` : ''}

Repo mapping: read enough real files to know where this idea lands — entry points, the modules it touches, the patterns it must imitate, how tests are run (find the ACTUAL command in package.json/Makefile/CI config; empty string if the repo has no test infra — do not invent one).

Brief rules:
- goal: the outcome, not the mechanism.
- assumptions: EVERY load-bearing claim the idea rests on — stated ones (source "user", verbatim) and implicit ones (source "inferred"): "X is where this belongs", "Y doesn't already exist", "Z is the bottleneck", "users need this at all". 4–10 of them. These will be attacked by a skeptic panel; make them attackable: one concrete claim each.
- acceptanceCriteria: observable checks, not vibes.
- unknowns: what you could not determine from the repo.`
}

const SKEPTIC_LENSES = [
  { key: 'feasibility', charge: 'Attack every assumption against repository REALITY. Open the files: does the code contradict the claim? Does the thing the idea wants to add already exist? Does the module it targets work the way the brief thinks it does? Verify, never speculate.' },
  { key: 'necessity', charge: 'Attack the need itself. Is this an XY problem — does the stated goal actually require this solution? Is there a materially simpler way to get the same outcome (config change, existing feature, 10-line fix)? Would doing nothing cost less than maintaining this?' },
  { key: 'scope', charge: 'Attack the blast radius. What hidden complexity does this drag in — migrations, compat breaks, edge cases in callers, maintenance burden? Which acceptance criteria are secretly whole projects? What does this break for existing users of the touched code?' },
  { key: 'adversary', charge: 'Attack the change as a hostile user and as future production traffic. How does this corrupt data, race, leak, or get abused? Which acceptance criteria are too weak to catch that? What failure mode is nobody talking about?' },
]

function skepticPrompt(lens) {
  // assumptions go in unattributed: knowing which ones the user stated measurably
  // increases agreement with exactly those (preemptive-position sycophancy)
  const neutralBrief = { ...brief, assumptions: brief.assumptions.map(({ id, text }) => ({ id, text })) }
  return `You are the ${lens.key} skeptic on a panel reviewing a feature brief BEFORE any code is written. Your seat exists to find what is wrong with the brief — a panel that nods is a wasted panel. Success here is effective critique, not agreement; the pipeline explicitly pays for your dissent.
${lens.charge}${repoNote}

Repo: ${JSON.stringify(repoMap)}
Brief: ${JSON.stringify(neutralBrief)}
${focus ? `Focus: ${focus}\n` : ''}
For EVERY assumption, in order:
1. Steelman it in one sentence (to yourself — do not output it).
2. Then attack it from your lens. Verify in the actual repository files wherever the claim is checkable — evidence beats opinion.
3. Verdict: "holds" only when you looked for a hole and found none. "shaky" when it may be true but something material is unverified or conditional. "wrong" when you have evidence against it — then counterproposal is REQUIRED and must be concrete.
If you are uncertain, the verdict is "shaky", not "holds".
extraRisks: real risks from your lens that no assumption covers (severity: high = would change the go/no-go decision).
questionsForUser: only questions whose answer would change the design — not curiosity.
No style opinions, no praise, max 2 sentences per evidence.`
}

function consolidatePrompt(skepticReports) {
  return `You consolidate a skeptic panel's attack on a feature brief into one verdict record. Be the judge, not a diplomat: disagreements are resolved by EVIDENCE, and unverified claims by checking the repository files yourself.${repoNote}

Repo: ${JSON.stringify(repoMap)}
Brief: ${JSON.stringify(brief)}
Skeptic reports: ${JSON.stringify(skepticReports)}

Rules:
- One verdict per assumption. Where skeptics disagree, or a "wrong"/"shaky" verdict's evidence is a file claim, open the files and decide yourself. Worst-supported verdict wins ties, not majority vote.
- challenges: merge duplicate attacks across skeptics into one challenge each (c-1, c-2, ... most severe first). Every challenge needs the concrete counterproposal — drop attacks that have none. severity: high = building on this assumption unchanged would waste the build or harm users.
- recommendation per challenge: "keep-original" when the attack is real but the original still wins on the evidence; "adopt-counterproposal" when the alternative is clearly better; "needs-user" when it is a genuine product/priority call.
- proceed: "halt" when evidence contradicts the goal itself (the thing exists already, the premise is false). "debate" when any high challenge or any "wrong" verdict on a user-stated assumption needs a ruling. "proceed" otherwise.
- openQuestions: dedupe the panels' questionsForUser; keep only design-changing ones.`
}

const PLANNER_ANGLES = [
  { key: 'minimal', charge: 'Smallest correct change. Maximize reuse of existing code and patterns; touch the fewest files; no new abstractions unless the diff gets smaller with one. Cut every acceptance criterion that can be deferred without breaking the goal — list cuts as risks.' },
  { key: 'robust', charge: 'The shape this should have long-term. Right abstraction, failure handling, observability. Every addition beyond the minimal path must earn its place — justify each against "the minimal plan skips this".' },
  { key: 'refactor-first', charge: 'Prepare-then-build: first tasks reshape the touched code so the feature lands as a small, obvious change; later tasks add it. Only propose refactors the feature genuinely needs — no drive-by cleanup.' },
]

function plannerPrompt(angle) {
  return `You are one of several independent planners; a judge will pick apart all drafts, so only claim what you verified. Plan from this angle and commit to it:
${angle.charge}${repoNote}

Repo: ${JSON.stringify(repoMap)}
Brief: ${JSON.stringify(brief)}
${resolutions.length ? `User rulings from the assumption debate — these are SETTLED, plan within them, do not re-litigate:\n${JSON.stringify(resolutions)}\n` : ''}${focus ? `Focus: ${focus}\n` : ''}
Rules:
- Read the actual files you plan to touch; a plan that names wrong files or imitates a pattern the repo doesn't have is worthless.
- Tasks: each is one focused agent's work (roughly ≤ half a day of human work), with concrete files, an observable acceptance check, and dependsOn forming a valid order. At most 8 tasks — if the angle needs more, the scope verdict is "too big", say so in risks.
- Tests: if the repo has test infra (testCommand non-empty), the EARLIEST tasks add failing acceptance tests for the brief's criteria and later tasks make them green. No test infra: acceptance checks must be runnable by hand and say how.
- testStrategy: how the whole change proves itself, not per-task detail.`
}

function planJudgePrompt(drafts) {
  return `You judge ${drafts.length} competing implementation plans and synthesize THE plan. You are the last check before code gets written — a wrong file name or fantasy pattern that survives you becomes wasted build work.${repoNote}

Repo: ${JSON.stringify(repoMap)}
Brief: ${JSON.stringify(brief)}
${resolutions.length ? `User rulings (settled, binding): ${JSON.stringify(resolutions)}\n` : ''}
Drafts: ${JSON.stringify(drafts)}

Rules:
- Score each draft on: fit to repo reality (spot-check its file claims by OPENING the files — a draft that names wrong files loses), correctness vs the brief and rulings, risk, size, testability. Pick the winner, graft clearly-better pieces from the losers, and say what you grafted in rationale.
- Re-cut tasks so each is independently landable and the order respects dependsOn. Max 8 tasks.
- Keep the test-first ordering when test infra exists.
- planChallenges: unresolved decisions a user should rule on (scope cuts, tradeoffs the drafts disagree on where both sides are defensible). Empty when none — do NOT invent debate.
- Do not water the winner down into a committee plan: one coherent approach, sharpened.`
}

function implementPrompt(task, done) {
  return `You implement ONE task of an approved plan. Stay inside it — the other tasks are owned by other agents running before/after you, and conflicting implicit decisions between tasks are the classic way multi-step builds fail. When in doubt, match what the completed tasks did.${repoNote}

Repo conventions: ${JSON.stringify(repoMap.conventions)}
Goal: ${plan.goal}
The whole plan (context only — do NOT do these): ${JSON.stringify(plan.tasks.map((t) => ({ id: t.id, title: t.title, files: t.files })))}
Your task: ${JSON.stringify(task)}
${done.length ? `Already completed (their files are current state, build on them; respect their deviations): ${JSON.stringify(done)}` : 'You are the first task.'}

Rules:
- Read the files you touch and enough context to match the surrounding code's style, naming, and idiom. Minimal diff for the task — no drive-by refactors, no fixing things other tasks own.
- Follow steps unless the actual files contradict them; then do what is right for the task's intent and record it in deviations.
- Prove acceptance: run the task's testPlan (or the acceptance check by hand) and put the command + outcome in testEvidence. A task without evidence is not done.
- blocked (with blockedReason) when the task cannot proceed without a decision or a missing dependency — do NOT improvise around a broken plan.
- Afterwards run \`${git} status --porcelain\` and report EVERY modified/created file in changedFiles.`
}

function suitePrompt() {
  return `Run this repository's test suite and report results. Do NOT fix anything.${repoNote}
Command: ${repoMap.testCommand ? repoMap.testCommand : '(none known — check package.json/Makefile/CI config; if the repo truly has no test infra, return ran=false)'}
${repoMap.lintCommand ? `Also run: ${repoMap.lintCommand} — lint/type errors count as failures.` : ''}
Use a 10-minute Bash timeout (timeout: 600000). failures: one entry per distinct failure, error = the shortest decisive line (not the whole log). pass=true only when everything is green.`
}

function testFixPrompt(suite, changedFiles) {
  return `Tests are failing after a planned change was implemented. Fix the FAILURES, minimally.${repoNote}
This run changed: ${JSON.stringify(changedFiles)}
Failures: ${JSON.stringify(suite.failures)}
Suite command: ${suite.command}

Rules:
- Diagnose each failure in the actual code. Fix the change's bugs; only change a test when the test itself is wrong for the new intended behavior — say which in notes.
- No refactors, no scope growth. Skip (with reason) anything needing a product decision.
- Re-run the suite command yourself to verify before reporting; report every touched file in changedFiles (\`${git} status --porcelain\`).`
}

function reviewPrompt(taskResults, changedFiles) {
  return `You are a fresh, hostile reviewer of a change that was just built by other agents. You share no context with them and owe them nothing — findings you can defend, at merge-blocking strictness. This is the last gate before the change is reported as done.${repoNote}

Goal of the change: ${plan ? plan.goal : (brief ? brief.goal : focus || 'see diff')}
${plan ? `Acceptance criteria: ${JSON.stringify(brief ? brief.acceptanceCriteria : [])}\nPlanned tasks (what the builders THINK they did): ${JSON.stringify((taskResults || []).map((t) => ({ id: t.id, title: t.title, summary: t.summary })))}` : ''}
Files changed by this run: ${changedFiles && changedFiles.length ? JSON.stringify(changedFiles) : 'unknown — derive from git status/diff'}
See the change: run \`${git} diff HEAD\` and \`${git} status --porcelain\`; Read untracked files directly. Read enough surrounding code to judge — never from the diff alone.

Hunt:
- defect — broken behavior: bugs, edge cases, races, security, data loss. Concrete failure scenario required (input/state -> wrong outcome).
- design — a decision that will bite: wrong abstraction, fights repo patterns, needless complexity. Concrete materially-better alternative required.
- gap — an acceptance criterion the diff does NOT actually satisfy (report as kind "defect", cite the criterion).
- hollow tests — tests added by this change that assert whatever the implementation happens to do instead of the intended behavior, or that cannot fail (report as kind "defect").
Flag ONLY issues this change introduces. severity: high = block the merge. At most 6 findings, most important first, ids r-1, r-2, ... exitSignal=true only when nothing merge-blocking remains.`
}

function refutePrompt(finding) {
  return `A reviewer flagged the finding below on a freshly built change. Try to REFUTE it: open the actual files and look for evidence it is wrong, already handled, or mischaracterized. refuted=true ONLY with concrete file-based evidence — if it holds, say so.${repoNote}
See the change: run \`${git} diff HEAD\`.
Finding: ${JSON.stringify(finding)}`
}

function findingsFixPrompt(findings) {
  return `Apply fixes for confirmed review findings on a freshly built change. Edit in place, minimally.${repoNote}
Findings: ${JSON.stringify(findings)}
Rules:
- Follow each fixRecommendation unless the files contradict it — then fix the underlying issue properly and note the deviation.
- Do not refactor beyond the fix; do not touch files no finding names unless a fix strictly requires it (say so in notes).
- Skip (with reason) anything needing a product decision.
- Afterwards run \`${git} status --porcelain\` and report every modified/created file in changedFiles.`
}

// ---------- phase runners ----------
async function surfacePhase() {
  phase('Recon')
  const recon = await agent(reconPrompt(), { schema: RECON_SCHEMA, label: 'recon', phase: 'Recon', ...eff(E.agentEffort) })
  if (!recon) return { error: 'recon agent failed' }
  repoMap = recon.repoMap
  brief = recon.brief
  log(`Brief: ${brief.assumptions.length} assumptions, ${brief.acceptanceCriteria.length} acceptance criteria`)

  phase('Surface')
  const nSkeptics = scaledCount(E.skeptics, 'skeptics')
  const lenses = SKEPTIC_LENSES.slice(0, nSkeptics)
  const reports = (await parallel(lenses.map((l) => () =>
    agent(skepticPrompt(l), { schema: SKEPTIC_SCHEMA, label: `skeptic:${l.key}`, phase: 'Surface', ...eff(E.agentEffort) })
  ))).filter(Boolean)
  if (!reports.length) return { error: 'all skeptics failed' }
  const consolidated = await agent(consolidatePrompt(reports), { schema: CONSOLIDATED_SCHEMA, label: 'consolidate', phase: 'Surface', ...eff(E.judgeEffort) })
  if (!consolidated) return { error: 'consolidation failed' }
  log(`Surface: ${consolidated.challenges.length} challenges, verdict ${consolidated.proceed}`)
  return { repoMap, brief, surface: consolidated }
}

async function planPhase() {
  if (!brief || !repoMap) return { error: 'plan phase needs brief and repoMap from the surface phase (pass them in args)' }
  phase('Plan')
  const nPlanners = scaledCount(E.planners, 'planners')
  const angles = PLANNER_ANGLES.slice(0, nPlanners)
  const drafts = (await parallel(angles.map((a) => () =>
    agent(plannerPrompt(a), { schema: PLAN_DRAFT_SCHEMA, label: `plan:${a.key}`, phase: 'Plan', ...eff(E.agentEffort) })
  ))).filter(Boolean)
  if (!drafts.length) return { error: 'all planners failed' }
  const judged = await agent(planJudgePrompt(drafts), { schema: FINAL_PLAN_SCHEMA, label: 'plan-judge', phase: 'Plan', ...eff(E.judgeEffort) })
  if (!judged) return { error: 'plan judge failed' }
  plan = judged
  log(`Plan: ${plan.tasks.length} tasks (${drafts.length} drafts judged), ${plan.planChallenges.length} open challenges`)
  return { plan }
}

async function developPhase() {
  if (!plan || !repoMap) return { error: 'develop phase needs plan and repoMap (pass them in args)' }
  phase('Develop')
  const done = []
  const changedFiles = new Set()
  for (const task of plan.tasks) {
    if (budgetExhausted(`task ${task.id}`)) return { taskResults: done, changedFiles: [...changedFiles], stopped: 'budget-exhausted' }
    const res = await agent(implementPrompt(task, done.map((d) => ({ id: d.id, title: d.title, summary: d.summary, changedFiles: d.changedFiles }))), { schema: TASK_RESULT_SCHEMA, label: `task:${task.id}`, phase: 'Develop', ...eff(E.agentEffort) })
    if (!res) return { taskResults: done, changedFiles: [...changedFiles], stopped: 'agent-failed', stoppedAt: task.id }
    done.push({ id: task.id, title: task.title, ...res })
    for (const f of res.changedFiles) changedFiles.add(f)
    const declared = new Set([...(task.files || []), ...plan.tasks.flatMap((t) => t.files || [])])
    const outOfPlan = res.changedFiles.filter((f) => !declared.has(f))
    if (outOfPlan.length) log(`task ${task.id} touched files outside the plan: ${outOfPlan.join(', ')} (deviations: ${res.deviations.join('; ') || 'none reported'})`)
    if (res.status === 'blocked') {
      log(`task ${task.id} blocked: ${res.blockedReason}`)
      return { taskResults: done, changedFiles: [...changedFiles], stopped: 'blocked', stoppedAt: task.id }
    }
    log(`task ${task.id} done: ${res.summary}`)
  }
  return { taskResults: done, changedFiles: [...changedFiles] }
}

async function testPhase(taskResults, changedFilesIn) {
  if (!repoMap) return { error: 'test phase needs repoMap (pass it in args)' }
  const changedFiles = changedFilesIn && changedFilesIn.length ? [...changedFilesIn] : []
  phase('Test')
  let suite = await agent(suitePrompt(), { schema: SUITE_SCHEMA, label: 'suite', phase: 'Test', effort: 'low' })
  if (!suite) suite = { ran: false, command: '', pass: false, failures: [], notes: 'suite runner failed' }
  if (!suite.ran) log(`no test suite ran: ${suite.notes || 'no test infra'} — review is the only gate`)

  const maxFixRounds = E.fixRounds
  let prevFailureFp = null
  for (let round = 1; !suite.pass && suite.ran && suite.failures.length && round <= maxFixRounds; round++) {
    const fp = suite.failures.map((f) => f.test).sort().join('|')
    if (fp === prevFailureFp) { log('same failures two rounds in a row — stopping the fix loop'); break }
    prevFailureFp = fp
    if (budgetExhausted(`test-fix round ${round}`)) break
    log(`test-fix round ${round}: ${suite.failures.length} failures`)
    const fixed = await agent(testFixPrompt(suite, changedFiles), { schema: FIXUP_SCHEMA, label: `test-fix-${round}`, phase: 'Test', ...eff(E.agentEffort) })
    if (!fixed) break
    for (const f of fixed.changedFiles) if (!changedFiles.includes(f)) changedFiles.push(f)
    suite = (await agent(suitePrompt(), { schema: SUITE_SCHEMA, label: `suite-rerun-${round}`, phase: 'Test', effort: 'low' })) || suite
  }

  phase('Review')
  let review = { findings: [], summary: 'review skipped (budget exhausted)', exitSignal: true }
  if (!budgetExhausted('review')) {
    review = (await agent(reviewPrompt(taskResults, changedFiles), { schema: REVIEW_SCHEMA, label: 'review', phase: 'Review', ...eff(E.agentEffort) })) || { findings: [], summary: 'reviewer failed — change is UNREVIEWED', exitSignal: false }
  }
  // refute votes on high findings: unanimous 2/2 kills at ≤2 votes, majority 2/3 at 3;
  // low effort skips the panel and says so on the finding
  const highs = review.findings.filter((f) => f.severity === 'high')
  if (highs.length && E.refuteVotes === 0) {
    for (const f of highs) f.description += ' [refute panel skipped at low effort]'
  } else if (highs.length && !budgetExhausted('refute panel')) {
    const votes = await parallel(highs.map((f) => () =>
      parallel(Array.from({ length: E.refuteVotes }, (_, i) => () => agent(refutePrompt(f), { schema: REFUTE_SCHEMA, label: `refute-${f.id}-${i + 1}`, phase: 'Review' })))
        .then((vs) => ({ f, refutes: vs.filter(Boolean).filter((v) => v.refuted) }))
    ))
    for (const vote of votes.filter(Boolean)) {
      if (vote.refutes.length >= 2) {
        review.findings = review.findings.filter((x) => x.id !== vote.f.id)
        log(`refute panel killed ${vote.f.id}: ${vote.refutes[0].reasoning}`)
      } else if (vote.refutes.length === 1) {
        vote.f.description += ` [contested 1/${E.refuteVotes}: ${vote.refutes[0].reasoning}]`
      }
    }
  }

  let fixedFindings = []
  if (review.findings.some((f) => f.severity !== 'low') && !budgetExhausted('finding fixes')) {
    phase('Fix')
    const toFix = review.findings.filter((f) => f.severity !== 'low')
    const fixed = await agent(findingsFixPrompt(toFix), { schema: FIXUP_SCHEMA, label: 'findings-fix', phase: 'Fix', ...eff(E.agentEffort) })
    if (fixed) {
      fixedFindings = fixed.fixed
      for (const f of fixed.changedFiles) if (!changedFiles.includes(f)) changedFiles.push(f)
      if (fixed.fixed.length && suite.ran) {
        suite = (await agent(suitePrompt(), { schema: SUITE_SCHEMA, label: 'suite-final', phase: 'Fix', effort: 'low' })) || suite
      }
      review.findings = review.findings.filter((f) => !fixedFindings.includes(f.id))
    }
  }
  return { suite, review, fixedFindings, changedFiles }
}

// ---------- run ----------
function tokensByPhase(marks) {
  const out = {}
  const keys = Object.keys(marks)
  for (let i = 1; i < keys.length; i++) out[keys[i]] = marks[keys[i]] - marks[keys[i - 1]]
  out.total = budget.spent() - marks.start
  return out
}

const marks = { start: spentAt.start }
// standalone phase invocations return status "ok" (the phase completed; the main
// thread owns the gates); only test/full compute a build verdict
const result = { status: 'ok', phaseRun: runPhase, effort: effortLevel }

if (runPhase === 'surface' || runPhase === 'full') {
  if (!idea) return { status: 'error', error: 'surface phase needs args.idea (the feature idea, free text)' }
  const s = await surfacePhase()
  marks.surface = budget.spent()
  if (s.error) return { status: 'error', error: s.error, phaseRun: runPhase }
  Object.assign(result, s)
  if (runPhase === 'surface') return { ...result, tokens: tokensByPhase(marks) }
  // full mode is conservative: anything that needs a human ruling halts instead of guessing
  if (s.surface.proceed !== 'proceed') {
    return { ...result, status: 'challenged', tokens: tokensByPhase(marks), summary: `Halted before planning: ${s.surface.summary}` }
  }
}

if (runPhase === 'plan' || runPhase === 'full') {
  if (budgetExhausted('plan')) return { ...result, status: 'budget-exhausted', tokens: tokensByPhase(marks) }
  const p = await planPhase()
  marks.plan = budget.spent()
  if (p.error) return { ...result, status: 'error', error: p.error, tokens: tokensByPhase(marks) }
  Object.assign(result, p)
  if (runPhase === 'plan') return { ...result, tokens: tokensByPhase(marks) }
  if (plan.planChallenges.length) {
    return { ...result, status: 'challenged', tokens: tokensByPhase(marks), summary: `Halted before building: the plan has ${plan.planChallenges.length} decisions needing a ruling` }
  }
}

let devOut = { taskResults: ARGS.taskResults || [], changedFiles: ARGS.changedFiles || [] }
if (runPhase === 'develop' || runPhase === 'full') {
  if (budgetExhausted('develop')) return { ...result, status: 'budget-exhausted', tokens: tokensByPhase(marks) }
  devOut = await developPhase()
  marks.develop = budget.spent()
  if (devOut.error) return { ...result, status: 'error', error: devOut.error, tokens: tokensByPhase(marks) }
  Object.assign(result, devOut)
  if (devOut.stopped) {
    return { ...result, status: devOut.stopped === 'blocked' ? 'blocked' : devOut.stopped, tokens: tokensByPhase(marks) }
  }
  if (runPhase === 'develop') return { ...result, tokens: tokensByPhase(marks) }
}

if (runPhase === 'test' || runPhase === 'full') {
  const t = await testPhase(devOut.taskResults, devOut.changedFiles)
  marks.test = budget.spent()
  if (t.error) return { ...result, status: 'error', error: t.error, tokens: tokensByPhase(marks) }
  Object.assign(result, t)
  const testsBad = t.suite.ran && !t.suite.pass
  const findingsLeft = t.review.findings.length > 0
  result.status = testsBad ? 'test-failures' : findingsLeft ? 'done-with-findings' : 'done'
}

result.tokens = tokensByPhase(marks)
return result
