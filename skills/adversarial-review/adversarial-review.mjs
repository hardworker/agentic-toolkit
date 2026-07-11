export const meta = {
  name: 'adversarial-review',
  description: 'Claude vs Codex adversarial debate review of any target: diff, working tree, docs, spec artifacts',
  whenToUse: 'Cross-model hostile review of code changes or planning documents. Hunts defects AND challenges design decisions. Independent reviews, cross-examination, verified synthesis; optional fix loop.',
  phases: [
    { title: 'Scope', detail: 'resolve what is under review' },
    { title: 'Review', detail: 'independent Claude + Codex reviews' },
    { title: 'Cross-Review', detail: 'each side attacks the other\'s findings' },
    { title: 'Synthesis', detail: 'judge verifies disputes in the files, confirms/rejects' },
    { title: 'Fix', detail: 'apply confirmed fixes (fix mode only)' },
  ],
}

// ---------- args ----------
const ARGS = (() => {
  if (typeof args !== 'string') return args || {}
  try { return JSON.parse(args) || {} } catch { return {} }
})()
// unified target; legacy args (mode/base/changeDir) still map onto it
const target = ARGS.target || ARGS.changeDir || ARGS.base || 'auto'
// optional absolute path to the repository root when it is not the session cwd
const repo = ARGS.repo || null
const git = repo ? `git -C ${repo}` : 'git'
const repoNote = repo ? `\nRepository root: ${repo} — file paths are relative to it; run every git command as \`${git} ...\` and Read files under that root.` : ''
const explicitFiles = Array.isArray(ARGS.files) && ARGS.files.length ? ARGS.files : null
const focus = ARGS.focus || ''
const fix = !!ARGS.fix
const solo = !!ARGS.solo
const maxIterations = fix ? Math.max(1, ARGS.maxIterations || 3) : 1

// ---------- schemas ----------
const ISSUE_PROPS = {
  id: { type: 'string', description: 'stable slug: <prefix>-<n>' },
  kind: { type: 'string', enum: ['defect', 'design'], description: 'defect = broken behavior; design = wrong/overcomplex decision or approach' },
  file: { type: 'string' },
  line: { type: 'integer' },
  severity: { type: 'string', enum: ['high', 'medium', 'low'] },
  title: { type: 'string' },
  description: { type: 'string', description: 'max 3 sentences. defect: concrete failure scenario (input/state -> wrong outcome). design: the concrete better alternative and why it is materially better' },
}
const ISSUE = { type: 'object', properties: ISSUE_PROPS, required: ['id', 'kind', 'file', 'severity', 'title', 'description'] }

const SCOPE_SCHEMA = {
  type: 'object',
  properties: {
    empty: { type: 'boolean' },
    files: { type: 'array', items: { type: 'string' } },
    summary: { type: 'string', description: 'one paragraph: what is under review' },
    diffCommand: { type: 'string', description: 'exact command reviewers run to see the changes; omit when reviewing files as-is' },
  },
  required: ['empty', 'files', 'summary'],
}

const REVIEW_SCHEMA = {
  type: 'object',
  properties: {
    issues: { type: 'array', items: ISSUE },
    summary: { type: 'string' },
    exitSignal: { type: 'boolean', description: 'true only when nothing worth fixing was found' },
    codexUnavailable: { type: 'string', description: 'codex runner only: error text when the codex CLI could not run' },
  },
  required: ['issues', 'summary', 'exitSignal'],
}

const CRITIQUE_SCHEMA = {
  type: 'object',
  properties: {
    verdicts: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          issueId: { type: 'string' },
          verdict: { type: 'string', enum: ['valid', 'invalid', 'uncertain'] },
          reasoning: { type: 'string', description: 'max 2 sentences, cite file:line' },
        },
        required: ['issueId', 'verdict', 'reasoning'],
      },
    },
    missedIssues: { type: 'array', items: ISSUE, description: 'real issues the other reviewer missed; ids <critic>-missed-<n>' },
    summary: { type: 'string' },
    codexUnavailable: { type: 'string' },
  },
  required: ['verdicts', 'missedIssues', 'summary'],
}

const SYNTHESIS_SCHEMA = {
  type: 'object',
  properties: {
    confirmed: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          ...ISSUE_PROPS,
          agreement: { type: 'string', enum: ['both', 'claude-only', 'codex-only'] },
          fixRecommendation: { type: 'string' },
        },
        required: ['id', 'kind', 'file', 'severity', 'title', 'description', 'agreement', 'fixRecommendation'],
      },
    },
    rejected: {
      type: 'array',
      items: {
        type: 'object',
        properties: { id: { type: 'string' }, reason: { type: 'string' } },
        required: ['id', 'reason'],
      },
    },
    exitSignal: { type: 'boolean' },
    summary: { type: 'string' },
  },
  required: ['confirmed', 'rejected', 'exitSignal', 'summary'],
}

const FIX_SCHEMA = {
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
    notes: { type: 'string' },
  },
  required: ['fixed', 'skipped'],
}

// ---------- prompts ----------
function scopePrompt() {
  return `You resolve the scope of a review. Do NOT review anything yourself.${repoNote}
Target spec: "${target}". Resolve it:
- "auto": run \`${git} status --porcelain\`; if there are uncommitted changes treat as "working-tree", else diff HEAD against the repo default branch (treat as a ref target).
- "working-tree": UNCOMMITTED changes only. files = changed/untracked paths. diffCommand = "${git} diff HEAD && ${git} status --porcelain" plus a note that untracked files must be Read directly. Do NOT widen the scope to the branch diff even if the uncommitted delta is tiny.
- a git ref: run \`${git} merge-base <ref> HEAD\`; files from \`${git} diff --name-status <mb>...HEAD\`; diffCommand = "${git} diff <mb>...HEAD". If the ref does not exist, fall back to the repo default branch and say so in summary.
- a directory or file path(s): files = those files (list a directory recursively; skip binaries and scaffolding like .openspec.yaml). No diffCommand — the files are reviewed as they stand. They may be code or documents (proposals, specs, designs).
Return empty=true only if nothing resolves. summary = one paragraph on what is under review (skim, do not judge).`
}

function reviewInstructions(scope, idPrefix) {
  const where = scope.diffCommand
    ? `Changed files: ${scope.files.join(', ')}\nSee the changes: run ${scope.diffCommand}`
    : `Files under review (read every one): ${scope.files.join(', ')}`
  return `You are one of two independent adversarial reviewers. The other works separately; you will cross-examine each other later, so only report findings you can defend.
${repoNote}
Target: ${scope.summary}
${where}
${focus ? `Focus: ${focus}\n` : ''}
Rules:
- Read the changes AND enough surrounding code/context to judge. Never judge from a diff alone. For documents, check claims against the actual codebase.
- Hunt TWO kinds of issue:
  * defect — broken behavior: bugs, broken edge cases, races, security, data loss, API misuse; in documents: contradictions, ambiguity an implementer cannot resolve, missing failure behavior, tasks/specs that do not cover the stated intent. Description = concrete failure scenario: input/state -> wrong outcome.
  * design — the decision itself is wrong: needless complexity, wrong abstraction, fights existing codebase patterns, unnecessary dependency, reinvented standard solution, a path that will bite later. Actively challenge the author's decisions — assume every major choice (data flow, abstraction, dependency, algorithm, API shape) is wrong until it survives scrutiny. Description = the concrete better alternative and why it is materially better here.
- No style nits, no praise, no "could be nicer" without a defensible alternative.
- severity: high = wrong behavior/data/security or a decision that locks in real damage; medium = real but limited; low = genuine but minor.
- At most 10 issues, most important first, description max 3 sentences each. Ids "${idPrefix}-<n>".
- exitSignal true ONLY if nothing worth fixing.`
}

function critiqueInstructions(scope, criticName, otherName, otherIssues) {
  return `You are cross-examining reviewer "${otherName}" in an adversarial review. Be skeptical BOTH ways: hallucinated findings must die, real ones must survive.
${repoNote}
Target: ${scope.summary}
${scope.diffCommand ? `See the changes: run ${scope.diffCommand}` : `Files: ${scope.files.join(', ')}`}

${otherName}'s findings:
${JSON.stringify(otherIssues)}

For EACH issue id, verify against the actual files — open them; never judge on plausibility.
- valid: real as described
- invalid: hallucinated, already handled, or mischaracterized — say exactly why, cite file:line. A design issue is invalid if its alternative is not materially better or not feasible in this codebase.
- uncertain: cannot be decided from the repository alone
Then list real issues ${otherName} MISSED — defects AND bad design decisions — only ones you can defend; ids "${criticName}-missed-<n>".`
}

function synthesisInstructions(scope, bundle) {
  return `You are the synthesis judge of an adversarial review between "claude" and "codex". Each finding below carries its critic's verdict. Produce the final verdict.
${repoNote}
Target: ${scope.summary}
${scope.diffCommand ? `See the changes: run ${scope.diffCommand}` : `Files: ${scope.files.join(', ')}`}

Debate record:
${JSON.stringify(bundle)}

Rules:
- Same underlying issue found by both sides: confirm once, agreement "both". Merge duplicates under one id, mention merged ids in description.
- criticVerdict "valid": confirm unless obviously wrong.
- criticVerdict "invalid", "uncertain", or "uncritiqued": VERIFY YOURSELF in the actual files before deciding — never confirm or reject an unvetted issue unchecked.
- missedIssues are candidates (agreement = the side that raised them); verify before confirming.
- design issues: confirm only if the alternative is feasible in this codebase and materially better — then it deserves the same weight as a defect, do not drop it as taste.
- Reject anything without a concrete failure scenario or concrete better alternative.
- Each confirmed issue gets a specific, actionable fixRecommendation.
- exitSignal true when confirmed is empty.`
}

function codexRunnerPrompt(innerPrompt, transcribeAs) {
  const transcription = {
    review: `Transcribe Codex's findings into the output schema exactly as stated — do not add, drop, soften, or verify anything yourself. Ids codex-1, codex-2, ... in Codex's order. exitSignal per Codex's own conclusion.`,
    critique: `Transcribe Codex's per-issue verdicts (valid/invalid/uncertain + reasoning) and missed issues exactly as stated — do not add, drop, soften, or verify anything yourself.`,
  }[transcribeAs]
  return `You are a runner for the Codex CLI. Do NOT review anything yourself — run Codex and faithfully transcribe its answer.

1. Write everything between the BEGIN/END markers (markers excluded) verbatim to a temp file (\`mktemp\`), using the Write tool.
2. Run, with a 10-minute Bash timeout (timeout: 600000):
   ${repo ? `cd ${repo} && ` : ''}codex exec --sandbox read-only - < <that temp file> 2>&1
   If it fails or Codex reports being blocked with an error mentioning code-mode host / codex-code-mode-host, retry ONCE adding --disable code_mode_host.
3. ${transcription}
4. If the codex binary is missing, unauthenticated, errors, or times out: return an empty result, summary explaining what happened, codexUnavailable = the exact error text. Do NOT substitute your own review.

---BEGIN CODEX PROMPT---
${innerPrompt}
---END CODEX PROMPT---`
}

const CODEX_REVIEW_FORMAT = `

Output format (follow exactly):
For each issue:
ISSUE <n>: <title>
KIND: defect|design
FILE: <path>:<line>
SEVERITY: high|medium|low
DESCRIPTION: <failure scenario or better alternative, max 3 sentences>
Finally:
ISSUES_FOUND: <n>
EXIT_SIGNAL: true|false   (true only if nothing worth fixing)`

const CODEX_CRITIQUE_FORMAT = `

Output format (follow exactly):
For each of the other reviewer's issue ids:
VERDICT <issueId>: valid|invalid|uncertain
REASONING: <max 2 sentences, file:line citations>
Then for each missed issue (if any):
MISSED ISSUE <n>: <title> / KIND / FILE / SEVERITY / DESCRIPTION`

// ---------- helpers ----------
const emptyCritique = { verdicts: [], missedIssues: [], summary: 'skipped (nothing to critique)' }

function threadIssues(issues, critique) {
  const v = new Map(critique.verdicts.map((x) => [x.issueId, x]))
  return issues.map((i) => ({
    ...i,
    criticVerdict: v.get(i.id) ? v.get(i.id).verdict : 'uncritiqued',
    criticReasoning: v.get(i.id) ? v.get(i.id).reasoning : '',
  }))
}

function fingerprintOf(confirmed) {
  return confirmed.map((i) => `${i.file}|${i.title}`).sort().join('\n')
}

// ---------- run ----------
phase('Scope')
let scope
if (explicitFiles) {
  scope = { empty: false, files: explicitFiles, summary: focus || `Explicit file list: ${explicitFiles.join(', ')}`, diffCommand: null }
} else {
  scope = await agent(scopePrompt(), { schema: SCOPE_SCHEMA, label: 'scope', phase: 'Scope', effort: 'low' })
}
if (!scope) return { status: 'error', error: 'scope agent failed' }
if (scope.empty || !scope.files.length) return { status: 'nothing-to-review', target }
log(`Reviewing ${scope.files.length} files (${solo ? 'solo' : 'claude+codex'}, ${fix ? 'fix loop, max ' + maxIterations : 'report-only'})`)

let codexAvailable = !solo
let prevFingerprint = null
const fixedAcrossIterations = []
let synthesis = null
let status = 'max-iterations'
let iterations = 0

for (let iter = 1; iter <= maxIterations; iter++) {
  iterations = iter
  const it = '#' + iter

  // independent reviews (barrier: cross-review needs both)
  const [claudeReviewRaw, codexReviewRaw] = await parallel([
    () => agent(reviewInstructions(scope, 'claude'), { schema: REVIEW_SCHEMA, phase: 'Review', label: 'claude-review' + it }),
    () => codexAvailable
      ? agent(codexRunnerPrompt(reviewInstructions(scope, 'codex') + CODEX_REVIEW_FORMAT, 'review'), { schema: REVIEW_SCHEMA, phase: 'Review', label: 'codex-review' + it, effort: 'low' })
      : Promise.resolve(null),
  ])
  const claudeReview = claudeReviewRaw || { issues: [], summary: 'claude reviewer unavailable', exitSignal: false }
  const codexReview = codexReviewRaw || { issues: [], summary: solo ? 'solo mode' : 'codex leg unavailable', exitSignal: false, codexUnavailable: solo ? '' : 'runner agent failed' }
  if (codexReview.codexUnavailable && codexAvailable) {
    codexAvailable = false
    log(`Codex unavailable — continuing single-model: ${codexReview.codexUnavailable}`)
  }
  log(`Iteration ${iter}: claude found ${claudeReview.issues.length}, codex found ${codexReview.issues.length}`)

  if (!claudeReview.issues.length && !codexReview.issues.length) {
    synthesis = { confirmed: [], rejected: [], exitSignal: true, summary: 'Both reviewers found nothing worth fixing.' }
    status = 'clean'
    break
  }

  // cross-review (skip a leg when nothing to critique or codex is down)
  const [claudeOnCodexRaw, codexOnClaudeRaw] = await parallel([
    () => codexReview.issues.length
      ? agent(critiqueInstructions(scope, 'claude', 'codex', codexReview.issues), { schema: CRITIQUE_SCHEMA, phase: 'Cross-Review', label: 'claude-on-codex' + it })
      : Promise.resolve(emptyCritique),
    // codex down or solo: a fresh claude critic stands in, so claude's findings never reach synthesis uncontested
    () => !claudeReview.issues.length
      ? Promise.resolve(emptyCritique)
      : codexAvailable
        ? agent(codexRunnerPrompt(critiqueInstructions(scope, 'codex', 'claude', claudeReview.issues) + CODEX_CRITIQUE_FORMAT, 'critique'), { schema: CRITIQUE_SCHEMA, phase: 'Cross-Review', label: 'codex-on-claude' + it, effort: 'low' })
        : agent(critiqueInstructions(scope, 'critic', 'claude', claudeReview.issues) + '\n\nYou are a fresh, independent stand-in for the unavailable second model. You share no context with the reviewer — critique with full hostility.', { schema: CRITIQUE_SCHEMA, phase: 'Cross-Review', label: 'self-critique' + it }),
  ])
  const claudeOnCodex = claudeOnCodexRaw || emptyCritique
  const codexOnClaude = codexOnClaudeRaw || emptyCritique
  if (codexOnClaude.codexUnavailable && codexAvailable) {
    codexAvailable = false
    log(`Codex became unavailable mid-debate: ${codexOnClaude.codexUnavailable}`)
  }

  // synthesis judges the threaded debate, verifying disputes in the files itself
  synthesis = await agent(
    synthesisInstructions(scope, {
      claudeIssues: threadIssues(claudeReview.issues, codexOnClaude),
      codexIssues: threadIssues(codexReview.issues, claudeOnCodex),
      missedByClaude: claudeOnCodex.missedIssues,
      missedByCodex: codexOnClaude.missedIssues,
    }),
    { schema: SYNTHESIS_SCHEMA, phase: 'Synthesis', label: 'synthesis' + it, effort: 'high' }
  )
  if (!synthesis) return { status: 'error', error: 'synthesis agent failed', target, iterations, codexAvailable, fixed: fixedAcrossIterations }
  log(`Synthesis ${it}: ${synthesis.confirmed.length} confirmed, ${synthesis.rejected.length} rejected`)

  if (!synthesis.confirmed.length) { status = 'clean'; break }
  if (!fix) { status = 'issues-found'; break }

  // circuit breaker: same confirmed set as last iteration -> stagnant
  const fp = fingerprintOf(synthesis.confirmed)
  if (fp === prevFingerprint) { status = 'stagnant'; break }
  prevFingerprint = fp

  const fixResult = await agent(
    `Apply fixes for the confirmed findings of an adversarial review. Edit the files under review (source code or documents) in place.
${repoNote}
Confirmed findings:
${JSON.stringify(synthesis.confirmed)}

Rules:
- Minimal, targeted fixes; follow each fixRecommendation unless the actual files contradict it — then fix the underlying issue properly and note the deviation.
- Do not refactor beyond the fix. Do not fix anything not listed.
- Skip (with reason) anything that turns out wrong or needs a product decision.`,
    { schema: FIX_SCHEMA, phase: 'Fix', label: 'fix' + it }
  )
  if (fixResult) {
    fixedAcrossIterations.push(...fixResult.fixed)
    log(`Fix ${it}: ${fixResult.fixed.length} fixed, ${fixResult.skipped.length} skipped`)
    if (!fixResult.fixed.length) { status = 'stagnant'; break }
  } else {
    log(`Fix ${it}: fixer agent failed; stopping`)
    status = 'error'
    break
  }
  // next iteration re-reviews the (now fixed) target
}

return {
  status, // clean | issues-found | stagnant | max-iterations | nothing-to-review | error
  target,
  iterations,
  codexAvailable,
  confirmed: synthesis ? synthesis.confirmed : [],
  rejected: synthesis ? synthesis.rejected : [],
  fixed: fixedAcrossIterations,
  summary: synthesis ? synthesis.summary : '',
}
