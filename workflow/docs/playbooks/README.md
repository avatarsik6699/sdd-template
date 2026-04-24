# Workflow Playbooks

These files are the **canonical source of truth** for the SDD workflow procedures.

In generated projects, runtime wrappers under `.claude/skills/` and `plugins/sdd-workflow/`
point here. In this template repository, shipped wrapper copies live under each template at
`templates/<template-id>/source/.claude/skills/` and
`templates/<template-id>/source/plugins/sdd-workflow/`.

To change a workflow, edit only these files. The runtime wrappers do not contain workflow logic.

Playbooks:

- [spec-init.md](./spec-init.md) — draft or refresh `docs/SPEC.md` from a product brief
- [phase-init.md](./phase-init.md) — scaffold a new `docs/PHASE_XX.md`
- [phase-gate.md](./phase-gate.md) — validate a phase before commit
- [spec-sync.md](./spec-sync.md) — propagate a `docs/SPEC.md` change
- [context-update.md](./context-update.md) — finalize a completed phase

Stack-specific gate dispatch for generated projects is defined by the installed template manifest
at `.sdd/template-manifest.yaml`. Resolve the active helper/docs pair with `sdd gate resolve`.
`docs/STACK.md#gate-commands` remains the human-readable command reference. In this template
repository, examples of that contract live under `templates/<template-id>/source/docs/STACK.md`.
Derived projects that swap stacks rewrite both the installed template manifest and `docs/STACK.md`;
the workflow playbook itself stays untouched.
