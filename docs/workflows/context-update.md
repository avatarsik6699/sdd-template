# Context Update

Purpose: update `docs/CONTEXT.md`, `docs/STATE.md`, and `docs/CHANGELOG.md` after a phase is completed.

Inputs:

- target phase number

Required reads:

- `docs/PHASE_XX.md`
- `docs/CONTEXT.md`
- `docs/STATE.md`
- `docs/CHANGELOG.md`

Procedure:

1. Confirm the phase is in progress or otherwise ready to finalize.
2. Extract the Contracts section from `docs/PHASE_XX.md`:
   - DB tables and columns
   - API endpoints
   - types and stores
   - env vars
3. Determine whether the change is:
   - no version bump
   - additive bump
   - breaking-contract bump
4. Update `docs/CONTEXT.md`:
   - version if needed
   - `captured_at`
   - completed and in-progress phase pointers
   - append-only contract arrays
   - migration head
   - notes
5. If a version bump happened, prepend a new entry to `docs/CHANGELOG.md`.
6. Mark the phase as done in `docs/STATE.md` and add a change-log row there.

Rules:

- never remove existing contract entries from arrays unless a deliberate breaking change requires it
- if the Contracts section is incomplete, stop and ask for correction
- do not commit automatically

Done when:

- `CONTEXT.md` matches what was built
- `STATE.md` marks the phase done
- `CHANGELOG.md` reflects any version bump
