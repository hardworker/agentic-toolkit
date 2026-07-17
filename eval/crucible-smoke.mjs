#!/usr/bin/env node
// Stub-runtime smoke test for skills/crucible/crucible.mjs.
// Executes the workflow script's control flow with canned agent responses —
// no real agents, no tokens. Run: node eval/crucible-smoke.mjs

import { readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const here = dirname(fileURLToPath(import.meta.url))
const src = readFileSync(join(here, '../skills/crucible/crucible.mjs'), 'utf8')

// workflow scripts run wrapped in an async function (top-level return is legal there)
const body = src.replace(/^export const meta/m, 'const meta')
const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor

// ---------- canned responses ----------
const RECON = {
  repoMap: { summary: 'demo repo', keyFiles: ['src/a.js'], conventions: 'esm modules', testCommand: 'npm test', lintCommand: '' },
  brief: {
    goal: 'add feature x', nonGoals: [], unknowns: [], constraints: [],
    assumptions: [
      { id: 'a-1', text: 'x does not exist yet', source: 'user' },
      { id: 'a-2', text: 'x belongs in src/a.js', source: 'inferred' },
    ],
    acceptanceCriteria: ['x works'],
  },
}
const SKEPTIC = { verdicts: [{ assumptionId: 'a-1', verdict: 'holds', evidence: 'checked src/a.js' }], extraRisks: [], questionsForUser: [], summary: 'ok' }
const CONSOLIDATED_OK = { assumptionVerdicts: [{ assumptionId: 'a-1', verdict: 'holds', evidence: 'verified' }], challenges: [], openQuestions: [], proceed: 'proceed', summary: 'nothing fundamental' }
const CONSOLIDATED_DEBATE = {
  assumptionVerdicts: [{ assumptionId: 'a-1', verdict: 'wrong', evidence: 'src/a.js:10 already implements x' }],
  challenges: [{ id: 'c-1', severity: 'high', assumptionId: 'a-1', title: 'x exists already', evidence: 'src/a.js:10', counterproposal: 'reuse it', recommendation: 'needs-user' }],
  openQuestions: [], proceed: 'debate', summary: 'needs a ruling',
}
const TASKS = [
  { id: 't-1', title: 'failing test', intent: 'lock intent', files: ['src/a.test.js'], steps: 'write test', acceptance: 'test fails', testPlan: 'npm test', dependsOn: [] },
  { id: 't-2', title: 'implement x', intent: 'make green', files: ['src/a.js'], steps: 'implement', acceptance: 'test passes', testPlan: 'npm test', dependsOn: ['t-1'] },
]
const DRAFT = { angle: 'minimal', tasks: TASKS, testStrategy: 'unit tests', risks: [], tradeoffs: 'none' }
const FINAL_PLAN = { goal: 'add feature x', tasks: TASKS, testStrategy: 'unit tests', risks: [], planChallenges: [], rationale: 'minimal won' }
const TASK_DONE = { status: 'done', changedFiles: ['src/a.js'], summary: 'implemented', testEvidence: 'npm test green', deviations: [] }
const TASK_BLOCKED = { status: 'blocked', changedFiles: [], summary: 'cannot proceed', testEvidence: '', deviations: [], blockedReason: 'missing dependency' }
const SUITE_PASS = { ran: true, command: 'npm test', pass: true, failures: [] }
const SUITE_FAIL = { ran: true, command: 'npm test', pass: false, failures: [{ test: 't1', error: 'boom' }] }
const REVIEW_CLEAN = { findings: [], summary: 'clean', exitSignal: true }
const REVIEW_HIGH = { findings: [{ id: 'r-1', kind: 'defect', file: 'src/a.js', line: 3, severity: 'high', title: 'bug', description: 'crashes on empty input', impact: 'all callers', fixRecommendation: 'guard input' }], summary: 'one high', exitSignal: false }
const REFUTE_NO = { refuted: false, reasoning: 'finding holds' }
const REFUTE_YES = { refuted: true, reasoning: 'pre-existing at src/a.js:1' }
const FIXUP = { fixed: ['r-1'], skipped: [], changedFiles: ['src/a.js'], notes: '' }

function responder(overrides = {}, sequences = {}) {
  const seq = {}
  return (label) => {
    for (const key of Object.keys(sequences)) {
      if (label.startsWith(key)) {
        const i = seq[key] ?? 0
        seq[key] = i + 1
        const arr = sequences[key]
        return arr[Math.min(i, arr.length - 1)]
      }
    }
    for (const key of Object.keys(overrides)) if (label.startsWith(key)) return overrides[key]
    if (label === 'recon') return RECON
    if (label.startsWith('skeptic:')) return SKEPTIC
    if (label === 'consolidate') return CONSOLIDATED_OK
    if (label.startsWith('plan:')) return DRAFT
    if (label === 'plan-judge') return FINAL_PLAN
    if (label.startsWith('task:')) return TASK_DONE
    if (label.startsWith('suite')) return SUITE_PASS
    if (label.startsWith('test-fix')) return FIXUP
    if (label === 'review') return REVIEW_CLEAN
    if (label.startsWith('refute-')) return REFUTE_NO
    if (label === 'findings-fix') return FIXUP
    return undefined
  }
}

// ---------- stub runtime ----------
async function run(args, { respond = responder(), budgetTotal = null, perAgentSpend = 10_000 } = {}) {
  const calls = []
  const logs = []
  const phases = []
  let spent = 0
  const budget = {
    total: budgetTotal,
    spent: () => spent,
    remaining: () => (budgetTotal == null ? Infinity : Math.max(0, budgetTotal - spent)),
  }
  const agent = async (prompt, opts = {}) => {
    const label = opts.label || 'unlabeled'
    calls.push(label)
    spent += perAgentSpend
    const r = respond(label, prompt)
    if (r === undefined) throw new Error(`no canned response for label "${label}"`)
    // fresh object per call, like the real runtime — the script may mutate results
    return r == null ? r : structuredClone(r)
  }
  const parallel = async (thunks) => {
    const out = []
    for (const t of thunks) { try { out.push(await t()) } catch { out.push(null) } }
    return out
  }
  const pipeline = async (items, ...stages) => {
    const out = []
    for (const [i, item] of items.entries()) {
      let v = item
      try { for (const s of stages) v = await s(v, item, i) } catch { v = null }
      out.push(v)
    }
    return out
  }
  const fn = new AsyncFunction('agent', 'parallel', 'pipeline', 'log', 'phase', 'budget', 'args', 'workflow', body)
  const result = await fn(agent, parallel, pipeline, (m) => logs.push(m), (t) => phases.push(t), budget, args, async () => { throw new Error('nested workflow() unavailable in smoke test') })
  return { result, calls, logs, phases }
}

// ---------- assertions ----------
let failures = 0
function check(name, cond, detail = '') {
  if (cond) { console.log(`  ok  ${name}`) } else { failures++; console.error(`FAIL  ${name}${detail ? ` — ${detail}` : ''}`) }
}
const has = (calls, prefix) => calls.filter((c) => c.startsWith(prefix)).length

// 1. full happy path
{
  const { result: r, calls, phases } = await run({ phase: 'full', idea: 'add feature x' })
  check('full: status done', r.status === 'done', r.status)
  check('full: brief + plan + tasks + suite + review present', !!(r.brief && r.plan && r.taskResults && r.suite && r.review))
  check('full: per-phase tokens reported', r.tokens && r.tokens.total > 0 && r.tokens.surface > 0 && r.tokens.test > 0, JSON.stringify(r.tokens))
  check('full: phase titles match meta', phases.every((p) => ['Recon', 'Surface', 'Plan', 'Develop', 'Test', 'Review', 'Fix'].includes(p)), phases.join(','))
  check('full: sequential tasks ran in order', calls.indexOf('task:t-1') < calls.indexOf('task:t-2'))
}

// 2. full halts when the surface verdict needs a ruling
{
  const { result: r, calls } = await run({ phase: 'full', idea: 'add x' }, { respond: responder({ consolidate: CONSOLIDATED_DEBATE }) })
  check('challenged: status', r.status === 'challenged', r.status)
  check('challenged: surface returned for the debate', r.surface && r.surface.challenges.length === 1)
  check('challenged: no planners spawned', has(calls, 'plan') === 0)
}

// 2e. effort low: smaller panels, no refute votes, one fix round, annotation instead
{
  const { result: r, calls } = await run(
    { phase: 'test', effort: 'low', plan: FINAL_PLAN, brief: RECON.brief, repoMap: RECON.repoMap, changedFiles: ['src/a.js'] },
    {
      respond: responder(
        { review: REVIEW_HIGH, 'findings-fix': { fixed: [], skipped: [{ id: 'r-1', reason: 'needs decision' }], changedFiles: [], notes: '' } },
        { suite: [SUITE_FAIL, SUITE_FAIL] },
      ),
    },
  )
  check('effort low: one fix round only', has(calls, 'test-fix') === 1, `${has(calls, 'test-fix')}`)
  check('effort low: refute panel skipped', has(calls, 'refute-') === 0)
  check('effort low: skipped panel annotated on the finding', r.review.findings[0]?.description.includes('skipped at low effort'))
  check('effort low: reported in result', r.effort === 'low', r.effort)
}

// 2f. effort xhigh: 3 refute votes, majority (2/3) kills
{
  const { result: r, calls } = await run(
    { phase: 'test', effort: 'xhigh', plan: FINAL_PLAN, brief: RECON.brief, repoMap: RECON.repoMap, changedFiles: ['src/a.js'] },
    { respond: responder({ review: REVIEW_HIGH }, { 'refute-': [REFUTE_YES, REFUTE_YES, REFUTE_NO] }) },
  )
  check('effort xhigh: 3 refute votes cast', has(calls, 'refute-') === 3, `${has(calls, 'refute-')}`)
  check('effort xhigh: majority refutation kills the finding', r.review.findings.length === 0 && r.status === 'done', r.status)
}

// 2g. --thorough is a legacy alias for effort high
{
  const { result: r, calls } = await run({ phase: 'surface', idea: 'add x', thorough: true })
  check('thorough alias: 4 skeptics', has(calls, 'skeptic:') === 4, `${has(calls, 'skeptic:')}`)
  check('thorough alias: effort high', r.effort === 'high', r.effort)
}

// 3. chained phase-by-phase invocations
{
  const s = await run({ phase: 'surface', idea: 'add x' })
  check('surface: status ok', s.result.status === 'ok', s.result.status)
  check('surface: no develop agents', has(s.calls, 'task:') === 0)
  const p = await run({ phase: 'plan', brief: s.result.brief, repoMap: s.result.repoMap, resolutions: [{ id: 'c-1', decision: 'keep-original' }] })
  check('plan: returns plan', p.result.status === 'ok' && p.result.plan.tasks.length === 2)
  const d = await run({ phase: 'develop', plan: p.result.plan, repoMap: s.result.repoMap })
  check('develop: all tasks done', d.result.status === 'ok' && d.result.taskResults.length === 2)
  const t = await run({ phase: 'test', plan: p.result.plan, brief: s.result.brief, repoMap: s.result.repoMap, taskResults: d.result.taskResults, changedFiles: d.result.changedFiles })
  check('test: verdict done', t.result.status === 'done', t.result.status)
}

// 4. blocked task stops the build
{
  const { result: r } = await run({ phase: 'develop', plan: FINAL_PLAN, repoMap: RECON.repoMap }, { respond: responder({ 'task:t-2': TASK_BLOCKED }) })
  check('blocked: status', r.status === 'blocked', r.status)
  check('blocked: stoppedAt t-2', r.stoppedAt === 't-2', r.stoppedAt)
  check('blocked: first task result kept', r.taskResults.length === 2 && r.taskResults[1].status === 'blocked')
}

// 5. stagnant test-fix loop stops instead of burning rounds
{
  const { result: r, calls } = await run(
    { phase: 'test', plan: FINAL_PLAN, repoMap: RECON.repoMap, changedFiles: ['src/a.js'] },
    { respond: responder({}, { suite: [SUITE_FAIL, SUITE_FAIL] }) },
  )
  check('stagnant fix loop: one fix attempt only', has(calls, 'test-fix') === 1, `${has(calls, 'test-fix')} attempts`)
  check('stagnant fix loop: status test-failures', r.status === 'test-failures', r.status)
}

// 6. refute panel kills a 2/2-refuted high finding
{
  const { result: r } = await run(
    { phase: 'test', plan: FINAL_PLAN, repoMap: RECON.repoMap, changedFiles: ['src/a.js'] },
    { respond: responder({ review: REVIEW_HIGH, 'refute-': REFUTE_YES }) },
  )
  check('refuted finding removed', r.review.findings.length === 0)
  check('refuted: status done', r.status === 'done', r.status)
}

// 7. surviving finding gets fixed and the suite re-runs
{
  const { result: r, calls } = await run(
    { phase: 'test', plan: FINAL_PLAN, repoMap: RECON.repoMap, changedFiles: ['src/a.js'] },
    { respond: responder({ review: { ...REVIEW_HIGH, findings: [...REVIEW_HIGH.findings] } }) },
  )
  check('finding fix applied', has(calls, 'findings-fix') === 1 && r.fixedFindings.includes('r-1'))
  check('suite re-ran after fix', has(calls, 'suite-final') === 1)
  check('fixed finding removed from report', r.review.findings.length === 0 && r.status === 'done', r.status)
}

// 8. budget: skeptic fan-out floors at 2, later phases stop cleanly
{
  const { result: r, calls } = await run({ phase: 'full', idea: 'add x' }, { budgetTotal: 100_000 })
  check('budget: skeptics floored at 2', has(calls, 'skeptic:') === 2, `${has(calls, 'skeptic:')} skeptics`)
  check('budget: run stopped as budget-exhausted', r.status === 'budget-exhausted', r.status)
  check('budget: no planners after exhaustion', has(calls, 'plan') === 0)
}

// 9. agent failure surfaces as error, not silence
{
  const { result: r } = await run({ phase: 'surface', idea: 'add x' }, { respond: responder({ recon: null }) })
  check('recon failure: status error', r.status === 'error' && /recon/.test(r.error), JSON.stringify(r))
}

// 10. static rules for workflow scripts
{
  check('no Date.now/new Date()/Math.random in script', !/Date\.now|Math\.random|new Date\(\)/.test(src))
  check('meta is a pure literal at the top', /^export const meta = \{/.test(src))
  check('missing idea rejected', (await run({ phase: 'full' })).result.status === 'error')
}

console.log(failures ? `\n${failures} FAILURE(S)` : '\nall smoke checks passed')
process.exit(failures ? 1 : 0)
