# Workflow Playbooks

These files are the **canonical source of truth** for the four SDD workflow procedures. Runtime wrappers (Claude Code skills under `.claude/skills/`, Codex plugin under `plugins/sdd-workflow/`) are thin stubs that point here.

To change a workflow, edit only these files. The runtime wrappers do not contain workflow logic.

Playbooks:

- [phase-init.md](./phase-init.md) — scaffold a new `docs/PHASE_XX.md`
- [phase-gate.md](./phase-gate.md) — validate a phase before commit
- [spec-sync.md](./spec-sync.md) — propagate a `docs/SPEC.md` change
- [context-update.md](./context-update.md) — finalize a completed phase

Stack-specific commands for `phase-gate` live in [../STACK.md → Gate Commands](../STACK.md#gate-commands). Derived projects that swap stacks rewrite that section; the workflow playbook itself stays untouched.
