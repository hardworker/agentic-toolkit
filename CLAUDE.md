# agentic-toolkit

Agent skills, each at `skills/<name>/SKILL.md` with support files beside it. Every skill is installable via `npx skills` and the Claude Code plugin marketplace.

## On any skill change

- Add a per-skill [CHANGELOG.md](CHANGELOG.md) entry: what changed and why. Keep a Changelog / SemVer format; bump that skill's version.
- Bump `version` in [.claude-plugin/plugin.json](.claude-plugin/plugin.json) too — it versions the repo as a whole, so every skill change moves it (new skill → minor).
- Sync [ARCHITECTURE.md](ARCHITECTURE.md) and [README.md](README.md) in the same change when behavior, args, pipeline, or the result contract move.

## Adding a skill

- `skills/<name>/SKILL.md` with valid frontmatter (`name`, `description`, `argument-hint`); support files beside it, not in a subdirectory.
- No `.claude-plugin/marketplace.json` edit: the repo is a single plugin with `source: "./"`, and both installers pick skills up by scanning for `SKILL.md`. A second entry pointing at `./` would install everything twice.
- Add to [README.md](README.md) and open a changelog section for it.
- Install locally the way the others are — symlink `~/.claude/skills/<name>` (and `~/.agents/skills/<name>` for Codex CLI) at `skills/<name>`, so edits go live with no update step.

## Git

Remote `hardworker/agentic-toolkit` is **public** — anything committed here is published. No absolute home paths, account/session ids, tokens, or machine-specific details in tracked files; use placeholders (`<skill-dir>`, `<accountId>`) and `~`.

Commit locally; never push without explicit per-push approval. History is linear and lands straight on `main` — no PRs, no merge commits.
