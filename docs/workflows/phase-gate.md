# Phase Gate

Purpose: run the validation checks for the current phase and produce an honest PASS or FAIL report that includes unresolved architect review notes.

Inputs:

- target phase number, or infer it from `docs/STATE.md`

Required reads:

- `docs/PHASE_XX.md`
- optionally `docs/STATE.md` if no phase number was given

Procedure:

1. Identify the target phase file.
2. Read the phase file's Gate Checks section.
3. Read the phase file's `Architect Review Notes` section and count unchecked items.
4. Verify infrastructure with `docker compose ps`.
5. Ensure `db` and `redis` are up and healthy. If needed, run `docker compose up -d db redis`.
6. Run backend tests.
7. Run `pnpm nuxt prepare` so `.nuxt/` types exist for frontend checks.
8. Run frontend type checks.
9. Run frontend unit tests.
10. Run Playwright e2e only if the full app stack is already up.
11. Run the smoke test from the phase file, or the default health check if none is specified.
12. Produce a table report with one row per check, include the architect review status, and return overall PASS only if automated checks are green and there are no unchecked architect review items.

Rules:

- do not edit files
- do not commit
- do not stop at the first failure; show the full picture
- do not auto-start the full app stack just to make Playwright look green
- do not treat unchecked architect review notes as informational; they block PASS until resolved

Done when:

- every required check has a reported status
- the output clearly says PASS or FAIL
- any unchecked architect review notes are listed explicitly in the report
