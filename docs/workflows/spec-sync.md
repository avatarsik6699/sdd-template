# Spec Sync

Purpose: propagate `docs/SPEC.md` changes across the operational documents and affected phase files.

Inputs:

- a brief description of what changed in `docs/SPEC.md`

Required reads:

- `docs/SPEC.md`
- `docs/CONTEXT.md`
- `docs/STATE.md`
- `docs/CHANGELOG.md`
- all `docs/PHASE_*.md`

Procedure:

1. Inspect the latest `docs/SPEC.md` changes.
2. Identify affected domains:
   - data model
   - API endpoints
   - frontend
   - non-functional requirements
   - phase plan
3. Map each changed domain to the affected `PHASE_XX.md` files.
4. Decide whether the contract changed and whether the version bump is additive, breaking, or none.
5. Prepend a new entry to `docs/CHANGELOG.md`.
6. Update `docs/CONTEXT.md` only if the technical contract changed.
7. Mark affected phases as `NEEDS_REVIEW` in `docs/STATE.md`.
8. Add a warning banner to each affected phase file and make surgical contract edits when the change is unambiguous.

Rules:

- never rewrite phase files from scratch
- prefer false positives over missed impact
- do not commit automatically
- preserve historical entries in `CHANGELOG.md`

Done when:

- impacted docs are synchronized
- affected phases are clearly marked for review
- unchanged phases remain untouched
