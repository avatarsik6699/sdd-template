# Phase Gate

Purpose: run the validation checks for the current phase and produce an honest PASS or FAIL report.

Inputs:

- target phase number, or infer it from `docs/STATE.md`

Required reads:

- `docs/PHASE_XX.md`
- optionally `docs/STATE.md` if no phase number was given

Procedure:

1. Identify the target phase file.
2. Read the phase file's Gate Checks section.
3. Verify infrastructure with `docker compose ps`.
4. Ensure `db` and `redis` are up and healthy. If needed, run `docker compose up -d db redis`.
5. Run backend tests.
6. Run `pnpm nuxt prepare` so `.nuxt/` types exist for frontend checks.
7. Run frontend type checks.
8. Run frontend unit tests.
9. Run Playwright e2e only if the full app stack is already up.
10. Run the smoke test from the phase file, or the default health check if none is specified.
11. Produce a table report with one row per check and an overall PASS or FAIL.

Rules:

- do not edit files
- do not commit
- do not stop at the first failure; show the full picture
- do not auto-start the full app stack just to make Playwright look green

Done when:

- every required check has a reported status
- the output clearly says PASS or FAIL
