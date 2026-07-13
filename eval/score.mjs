#!/usr/bin/env node
// Usage: node score.mjs <manifest.json> <result.json> [tokens]
// Scores an adversarial-review run against a fixture manifest. See eval/README.md.
import { readFileSync } from 'node:fs'

const [manifestPath, resultPath, tokens] = process.argv.slice(2)
if (!manifestPath || !resultPath) {
  console.error('usage: node score.mjs <manifest.json> <result.json> [subagent-tokens]')
  process.exit(1)
}
const manifest = JSON.parse(readFileSync(manifestPath, 'utf8'))
const result = JSON.parse(readFileSync(resultPath, 'utf8'))
const confirmed = result.confirmed || []
const known = manifest.known || []

const norm = (f) => f.replace(/^\.\//, '')
const inFile = (finding, file) => norm(finding.file).endsWith(norm(file)) || norm(file).endsWith(norm(finding.file))

const found = manifest.seeded.filter((s) => confirmed.some((c) => inFile(c, s.file)))
const missed = manifest.seeded.filter((s) => !found.includes(s))
const falsePos = confirmed.filter((c) => (manifest.cleanFiles || []).some((f) => inFile(c, f)))
const knownHits = confirmed.filter((c) => known.some((k) => inFile(c, k.file) && !manifest.seeded.some((s) => inFile(c, s.file))))
const unknown = confirmed.filter((c) => !found.some((s) => inFile(c, s.file)) && !falsePos.includes(c) && !knownHits.includes(c))

const pct = (a, b) => (b ? ((100 * a) / b).toFixed(0) + '%' : 'n/a')
console.log(`fixture: ${manifest.name}   status: ${result.status}   iterations: ${result.iterations}   codex: ${result.codexAvailable}`)
console.log(`recall:    ${found.length}/${manifest.seeded.length} (${pct(found.length, manifest.seeded.length)})`)
missed.forEach((s) => console.log(`  MISSED  ${s.file} — ${s.hint}`))
console.log(`falsePos:  ${falsePos.length} in cleanFiles`)
falsePos.forEach((c) => console.log(`  FP      ${c.file} — ${c.title}`))
console.log(`known:     ${knownHits.length} re-found (pre-triaged real issues)`)
console.log(`unknown:   ${unknown.length} — triage by hand, then add to manifest as "known" or count as FP`)
unknown.forEach((c) => console.log(`  ?       [${c.severity}/${c.kind}] ${c.file} — ${c.title}`))
if (tokens) console.log(`tokens:    ${tokens}`)
