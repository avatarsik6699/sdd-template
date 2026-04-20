# Phase Init

Purpose: scaffold a new `docs/PHASE_XX.md` from `docs/PHASE_TEMPLATE.md` using `docs/SPEC.md`, and append the phase row to `docs/STATE.md`.

Inputs:

- target phase number

Required reads:

- `docs/PHASE_TEMPLATE.md`
- `docs/CONTEXT.md`
- `docs/STATE.md`
- `docs/SPEC.md`

Procedure:

1. Normalize the phase number to two digits.
2. If `docs/PHASE_XX.md` already exists, ask before overwriting.
3. Confirm the previous phase is complete, unless creating `PHASE_01`.
4. Extract from `docs/SPEC.md`:
   - phase title and scope from the phase plan
   - new DB tables for this phase
   - new API endpoints for this phase
   - new types and stores implied by the data model and frontend sections
   - file list for backend, frontend, and infra
   - environment variables introduced for the first time
5. Create `docs/PHASE_XX.md` from the template and fill scope, files, contracts, and atomic commit message.
6. Append a `PHASE_XX` row to the phase status table in `docs/STATE.md`.

Rules:

- never modify `docs/SPEC.md`
- never modify `docs/CONTEXT.md`
- make best-effort extractions instead of leaving whole sections blank
- use `[TODO: verify]` only when a specific detail is genuinely absent

Done when:

- `docs/PHASE_XX.md` exists and is filled from `docs/SPEC.md`
- `docs/STATE.md` contains the new pending row
