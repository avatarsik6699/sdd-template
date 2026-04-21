---
name: phase-gate
description: Run the full SDD gate for a phase: infrastructure checks, tests, e2e, smoke verification, and architect review notes verification. Use when the user asks whether a phase is ready to commit.
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
      - "typecheck"
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

Execute the canonical playbook in [docs/workflows/phase-gate.md](../../../../docs/workflows/phase-gate.md). Stack-specific commands are dispatched from [docs/STACK.md → Gate Commands](../../../../docs/STACK.md#gate-commands).

Read-only: do not edit code, do not commit. Do not return PASS while unchecked architect review notes remain.
