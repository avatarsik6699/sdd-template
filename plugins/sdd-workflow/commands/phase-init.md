---
description: Initialize a new SDD phase document from PHASE_TEMPLATE, SPEC, CONTEXT, and STATE. Usage: /phase-init 02
---

# /phase-init

Initialize a new phase document for this repository's SDD workflow.

## Preflight

1. Confirm the target phase number from the command arguments.
2. Check whether `docs/PHASE_XX.md` already exists.
3. Read:
   - `docs/PHASE_TEMPLATE.md`
   - `docs/SPEC.md`
   - `docs/CONTEXT.md`
   - `docs/STATE.md`

## Plan

1. Derive the phase title and scope from `docs/SPEC.md`.
2. Extract the contracts, files, and env vars relevant to that phase.
3. Create or refresh `docs/PHASE_XX.md`.
4. Append the phase row to `docs/STATE.md`.

## Commands

This command is documentation-driven. Follow the canonical playbook:

- `docs/workflows/phase-init.md`

Use the matching skill:

- `skills/phase-init/SKILL.md`

## Verification

Confirm that:

- `docs/PHASE_XX.md` exists
- placeholders were replaced with concrete content
- `docs/STATE.md` contains the new phase row

## Summary

Report:

- created or refreshed phase file
- derived scope summary
- contracts filled
- any `[TODO: verify]` markers left behind

## Next Steps

Suggest the next natural action:

- implement the phase
- or run `/phase-gate XX` after implementation
