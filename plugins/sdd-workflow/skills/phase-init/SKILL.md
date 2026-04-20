---
name: phase-init
description: Initialize a new SDD phase document from SPEC, CONTEXT, STATE, and PHASE_TEMPLATE. Use when the user wants to scaffold or refresh a PHASE_XX.md file.
metadata:
  priority: 5
  pathPatterns:
    - 'docs/PHASE_TEMPLATE.md'
    - 'docs/PHASE_*.md'
    - 'docs/SPEC.md'
    - 'docs/STATE.md'
    - 'docs/CONTEXT.md'
  promptSignals:
    phrases:
      - "phase init"
      - "initialize phase"
      - "create phase doc"
      - "scaffold phase"
    allOf:
      - [phase, init]
      - [phase, scaffold]
    anyOf:
      - "phase"
      - "phase document"
      - "phase file"
    noneOf: []
    minScore: 6
retrieval:
  aliases:
    - sdd phase init
    - phase bootstrap
  intents:
    - create a phase document
    - scaffold next phase
  entities:
    - PHASE_TEMPLATE.md
    - SPEC.md
    - STATE.md
---

# phase-init

Canonical portable playbook: `docs/workflows/phase-init.md`

Use this skill to create or refresh `docs/PHASE_XX.md` from the project contract.

Workflow:

1. Validate and normalize the phase number.
2. Read `docs/PHASE_TEMPLATE.md`, `docs/CONTEXT.md`, `docs/STATE.md`, and `docs/SPEC.md`.
3. Confirm the previous phase is complete or explicitly note the risk.
4. Extract the target phase title, scope, contracts, file list, and env vars from `docs/SPEC.md`.
5. Create `docs/PHASE_XX.md` with filled placeholders and a concrete atomic commit message.
6. Append the phase row to `docs/STATE.md`.
7. Report exactly what was created and what still needs verification.

Rules:

- Never modify `docs/SPEC.md`.
- Never modify `docs/CONTEXT.md`.
- Use `[TODO: verify]` only when the source material genuinely does not provide the detail.
- Prefer exact extraction from `docs/SPEC.md` over paraphrasing.
- Do not commit.
