---
description: Propagate SPEC.md changes into CONTEXT, STATE, CHANGELOG, and affected PHASE files. Usage: /spec-sync "what changed"
---

# /spec-sync

Synchronize downstream SDD docs after a change to `docs/SPEC.md`.

## Preflight

1. Read:
   - `docs/SPEC.md`
   - `docs/CONTEXT.md`
   - `docs/STATE.md`
   - `docs/CHANGELOG.md`
   - all `docs/PHASE_*.md`
2. Inspect the recent diff for `docs/SPEC.md`.
3. Capture the user-provided description of the spec change.

## Plan

1. Determine which domains changed.
2. Identify which phases are impacted.
3. Update `CHANGELOG.md`.
4. Update `CONTEXT.md` if the technical contract changed.
5. Mark affected phases for review.
6. Patch only the impacted phase files.

## Commands

Follow the canonical playbook:

- `docs/workflows/spec-sync.md`

Use the matching skill:

- `skills/spec-sync/SKILL.md`

## Verification

Confirm:

- affected phases are marked `NEEDS_REVIEW` where appropriate
- `CONTEXT.md` only changed when justified
- `CHANGELOG.md` has a new top entry

## Summary

Report:

- version bump or no bump
- affected phases
- patched phase files
- unaffected phases

## Next Steps

- tell the user which phases must be reviewed before further implementation
