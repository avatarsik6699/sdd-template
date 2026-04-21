# Claude Code adapter — `sdd-template` repository

**Start here:** read [`AGENTS.md`](AGENTS.md). It is the source of truth for working on this repo.

This file adds only Claude-specific notes.

## Scope reminder

This repo IS the template. Do not run `/phase-gate`, `/phase-init`, `/spec-sync`, or `/context-update` against this repo's `docs/` — those skills are shipped to derived projects. Test them in a scratch directory.

## Skills defined here (shipped to derived projects)

| Skill | Canonical playbook |
|-------|--------------------|
| `/phase-init` | [`docs/workflows/phase-init.md`](docs/workflows/phase-init.md) |
| `/phase-gate` | [`docs/workflows/phase-gate.md`](docs/workflows/phase-gate.md) |
| `/spec-sync` | [`docs/workflows/spec-sync.md`](docs/workflows/spec-sync.md) |
| `/context-update` | [`docs/workflows/context-update.md`](docs/workflows/context-update.md) |

The files under `.claude/skills/*/SKILL.md` and `plugins/sdd-workflow/{skills,commands}/` are thin wrappers pointing at the playbooks above. To change workflow behavior, edit the playbook — never the wrapper.
