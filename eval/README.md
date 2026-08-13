# adversarial-review eval harness

Measures precision / recall / cost of the skill against fixtures with **known seeded bugs**, so prompt and pipeline changes are validated by numbers instead of vibes.

## Protocol

1. **Build a fixture** — a small git repo (or branch of a real one) where a diff introduces N known issues. Record them in a `manifest.json` next to the fixture:

```jsonc
{
  "name": "auth-refactor-seeded",
  "repo": "/abs/path/to/fixture-repo",
  "target": "main",                 // the target argument for the run
  "seeded": [                       // ground truth
    { "file": "src/auth.ts", "hint": "token expiry uses < instead of <=", "kind": "defect" },
    { "file": "src/db.ts",   "hint": "connection pool never released on error path", "kind": "defect" }
  ],
  "cleanFiles": ["src/util.ts"]     // files with NO seeded issues — findings here count against precision
}
```

   The cheapest way to seed: ask a model to inject N subtle bugs into a healthy diff and write the manifest for you, then eyeball it. Keep fixtures small (≤10 files) so runs are cheap; a `--no-codex` run is usually enough for regression purposes.

2. **Run the skill** on the fixture (`--cwd <repo>` plus the target). It writes a run record to a temp file and reports the path; copy that into `results/<fixture>-<variant>.json`.

3. **Score**: `node eval/score.mjs manifest.json results/run.json <subagent-tokens>`

## Scoring

`score.mjs` matches confirmed findings to seeded issues **by file** (a seeded issue counts as found if any confirmed finding lands in its file — hints are for human review of near-misses) and reports:

- **recall** — seeded issues found / seeded
- **precision proxy** — confirmed findings in seeded files / all confirmed (findings in `cleanFiles` are hard false positives; findings elsewhere are "unknown" — triage by hand once, then add them to the manifest as `known` so reruns score them automatically)
- **cost** — not currently measurable per run: the session usage report covers the whole session rather than the review, and Codex CLI tokens are spent in another process entirely. Compare recall and false positives; treat the third argument as a rough note.

## What to compare

Run the same fixture across variants before/after a pipeline change: `--no-codex` vs duo, `--strict` vs default, prompt tweaks. A change that drops recall on seeded bugs or floods `cleanFiles` with findings is a regression, whatever it feels like.
