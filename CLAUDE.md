# Claude Code adapter — `sdd-template` repository

**Start here:** read [`AGENTS.md`](AGENTS.md). It is the source of truth for working on this repo.

This file adds only Claude-specific notes.

## Scope reminder

This repo IS the template. Do not run `/phase-gate`, `/phase-init`, `/spec-sync`, or `/context-update` against this repo's `docs/` — those skills are shipped to derived projects. Test them in a scratch directory.

## Skills shipped from this repo

| Skill | Canonical playbook |
|-------|--------------------|
| `/phase-init` | [`workflow/docs/playbooks/phase-init.md`](workflow/docs/playbooks/phase-init.md) |
| `/phase-gate` | [`workflow/docs/playbooks/phase-gate.md`](workflow/docs/playbooks/phase-gate.md) |
| `/spec-sync` | [`workflow/docs/playbooks/spec-sync.md`](workflow/docs/playbooks/spec-sync.md) |
| `/context-update` | [`workflow/docs/playbooks/context-update.md`](workflow/docs/playbooks/context-update.md) |

The shipped files under `templates/<template-id>/source/.claude/skills/` and
`templates/<template-id>/source/plugins/sdd-workflow/` are thin wrappers pointing at the
playbooks above. To change workflow behavior, edit the playbook, never the wrapper.
