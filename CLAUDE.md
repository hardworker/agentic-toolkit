# agentic-toolkit

Agent skills, each at `skills/<name>/SKILL.md` with support files beside it. Every skill is installable via `npx skills` and the Claude Code plugin marketplace.

## On any skill change

- Add a per-skill [CHANGELOG.md](CHANGELOG.md) entry: what changed and why. Keep a Changelog / SemVer format; bump that skill's version.
- Sync [ARCHITECTURE.md](ARCHITECTURE.md) and [README.md](README.md) in the same change when behavior, args, pipeline, or the result contract move.

## Adding a skill

- `skills/<name>/SKILL.md` with valid frontmatter (`name`, `description`); support files beside it.
- Register in `.claude-plugin/marketplace.json` as its own plugin so `npx skills add hardworker/agentic-toolkit` and the marketplace both install it.
- Add to [README.md](README.md) and open a changelog section for it.

## Git

Remote `hardworker/agentic-toolkit` is private. Commit locally; never push without explicit per-push approval.
