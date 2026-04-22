# Phase Gate

Purpose: run the validation checks for the current phase and produce an honest PASS or FAIL report that includes unresolved architect review notes.

Inputs:

- target phase number, or infer it from `docs/STATE.md`

Required reads:

- `docs/PHASE_XX.md`
- `docs/STACK.md` (`Gate Commands` section)
- optionally `docs/STATE.md` if no phase number was given

Procedure:

1. Identify the target phase file.
2. Read the phase file's Gate Checks section.
3. Read `docs/STACK.md#gate-commands` and treat it as the authoritative command source for the standard gate steps.
4. Read the phase file's `Architect Review Notes` section and count unchecked items.
5. Ensure a project `.env` exists so Docker Compose and containerized commands use the same credentials the app uses.
6. Run the stack command listed for infrastructure/bootstrap and verify the services are ready.
7. Run the migrations command from `docs/STACK.md`.
8. Run the backend test command from `docs/STACK.md`.
9. Run the frontend prep command from `docs/STACK.md`.
10. Run the frontend typecheck command from `docs/STACK.md`.
11. Run the frontend unit test command from `docs/STACK.md`.
12. Run the E2E anti-flake lint command from `docs/STACK.md` (must fail on committed `waitForTimeout` usage).
13. Run the e2e command from `docs/STACK.md` (Chromium is the single deterministic pass/fail browser for the reference stack).
14. Run the smoke command from `docs/STACK.md`, unless the phase file defines a phase-specific smoke override.
15. Produce a table report with one row per check, include the architect review status, and return overall PASS only if automated checks are green and there are no unchecked architect review items.

Rules:

- do not edit files
- do not commit
- do not stop at the first failure; show the full picture
- do use the repository's `.env` when bringing up Docker services or running containerized checks
- do bring up the full stack yourself; the gate should verify the real end-to-end environment
- do not treat unchecked architect review notes as informational; they block PASS until resolved
- if the stack changes, update `docs/STACK.md`, not this workflow

Preferred command:

```bash
./scripts/phase-gate.sh [XX]
```

For the FastAPI + Nuxt reference stack, the helper above implements the `Gate Commands` contract. If you cannot use the helper script in the current runtime, follow the same sequence manually by reading `docs/STACK.md`.

Done when:

- every required check has a reported status
- the output clearly says PASS or FAIL
- any unchecked architect review notes are listed explicitly in the report
