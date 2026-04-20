---
description: Run the SDD gate checks for a phase. Usage: /phase-gate 01
---

# /phase-gate

Run the repository's gate checks and return an honest PASS/FAIL report.

## Preflight

1. Resolve the phase number from arguments or `docs/STATE.md`.
2. Read `docs/PHASE_XX.md`.
3. Note any phase-specific Gate Checks listed there.

## Plan

1. Check container health.
2. Run backend validation, then `pnpm nuxt prepare`, frontend type-check, and frontend unit tests.
3. Run Playwright only if the full stack is already healthy.
4. Run the smoke test.
5. Summarize everything in one gate report.

## Commands

Follow the canonical playbook:

- `docs/workflows/phase-gate.md`

Use the matching skill:

- `skills/phase-gate/SKILL.md`

## Verification

Confirm that every expected check produced a result row, even if some failed.

## Summary

Return:

- Docker status
- pytest status
- `nuxt prepare` status
- frontend type-check status
- vitest status
- Playwright status
- smoke test status
- overall PASS/FAIL

## Next Steps

- If PASS: say it is safe to commit.
- If FAIL: list the concrete failing checks and likely fixes.
