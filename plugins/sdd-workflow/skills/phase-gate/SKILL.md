---
name: phase-gate
description: Run the full SDD gate for a phase: infrastructure checks, tests, e2e, and smoke verification. Use when the user asks whether a phase is ready to commit.
metadata:
  priority: 5
  pathPatterns:
    - 'docs/PHASE_*.md'
    - 'docs/STATE.md'
    - 'frontend/playwright.config.ts'
    - 'frontend/test-results/**'
    - 'frontend/playwright-report/**'
    - 'docker-compose.yml'
  bashPatterns:
    - '\bdocker compose\b'
    - '\bpytest\b'
    - '\bpnpm\b'
    - '\bvitest\b'
  promptSignals:
    phrases:
      - "phase gate"
      - "run gate checks"
      - "ready to commit"
      - "check phase readiness"
    allOf:
      - [phase, gate]
      - [gate, checks]
    anyOf:
      - "pytest"
      - "tsc"
      - "playwright"
    noneOf: []
    minScore: 6
retrieval:
  aliases:
    - sdd gate
    - phase verification
  intents:
    - verify a phase before commit
    - run project gate checks
  entities:
    - docker compose
    - pytest
    - vitest
    - playwright
---

# phase-gate

Canonical portable playbook: `docs/workflows/phase-gate.md`

Use this skill when the user wants an honest PASS/FAIL view of the current phase.

Workflow:

1. Resolve the target phase from arguments or from `docs/STATE.md`.
2. Read the phase file's Gate Checks section.
3. Check Docker infrastructure state.
4. Run backend tests.
5. Run TypeScript checks.
6. Run frontend unit tests.
7. Run Playwright end-to-end tests only if the full stack is already up.
8. Run the smoke check.
9. Produce a structured gate report with PASS/FAIL and exact failing areas.

Rules:

- Do not edit code.
- Do not commit.
- Do not hide failures behind early exit when later checks can still provide useful signal.
- If e2e preconditions are missing, report that clearly rather than masking it.
