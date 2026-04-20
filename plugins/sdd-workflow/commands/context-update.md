---
description: Update CONTEXT.md, STATE.md, and CHANGELOG.md after a completed phase. Usage: /context-update 01
---

# /context-update

Synchronize the SDD contract docs after a phase is complete.

## Preflight

1. Resolve the target phase.
2. Read:
   - `docs/PHASE_XX.md`
   - `docs/CONTEXT.md`
   - `docs/STATE.md`
   - `docs/CHANGELOG.md`

## Plan

1. Inspect the phase Contracts section.
2. Decide whether the contract version needs a bump.
3. Update `CONTEXT.md`.
4. Update `STATE.md`.
5. Add a `CHANGELOG.md` entry when needed.

## Commands

Follow the canonical playbook:

- `docs/workflows/context-update.md`

Use the matching skill:

- `skills/context-update/SKILL.md`

## Verification

Confirm:

- `docs/STATE.md` marks the phase done
- the version bump decision is reflected consistently
- `docs/CHANGELOG.md` matches the `CONTEXT.md` version outcome

## Summary

Report:

- old and new context versions
- whether changelog entry was added
- next phase to initialize

## Next Steps

- suggest `/phase-init [next]` when appropriate
