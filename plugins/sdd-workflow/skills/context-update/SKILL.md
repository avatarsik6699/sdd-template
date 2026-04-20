---
name: context-update
description: Synchronize CONTEXT, STATE, and CHANGELOG after a completed phase. Use when a phase has landed and the contract docs must reflect reality.
metadata:
  priority: 5
  pathPatterns:
    - 'docs/PHASE_*.md'
    - 'docs/CONTEXT.md'
    - 'docs/STATE.md'
    - 'docs/CHANGELOG.md'
  promptSignals:
    phrases:
      - "context update"
      - "update context"
      - "sync context"
      - "phase complete"
    allOf:
      - [context, update]
      - [sync, context]
    anyOf:
      - "changelog"
      - "state"
      - "contract"
    noneOf: []
    minScore: 6
retrieval:
  aliases:
    - update context md
    - sync docs after phase
  intents:
    - update contract docs after implementation
    - mark a phase done
  entities:
    - CONTEXT.md
    - STATE.md
    - CHANGELOG.md
---

# context-update

Canonical portable playbook: `docs/workflows/context-update.md`

Use this skill after a phase has been completed and the docs need to catch up.

Workflow:

1. Read `docs/PHASE_XX.md`, `docs/CONTEXT.md`, `docs/STATE.md`, and `docs/CHANGELOG.md`.
2. Confirm the phase is actually ready to be finalized.
3. Extract the Contracts section from the phase file.
4. Determine whether the change is additive, breaking, or docs-only.
5. Update `docs/CONTEXT.md` surgically.
6. Add a `docs/CHANGELOG.md` entry when the contract version changes.
7. Mark the phase done in `docs/STATE.md`.
8. Report the version bump decision and next step.

Rules:

- Never remove existing historical context entries unless the source of truth explicitly requires it.
- Only append to contract arrays when the change is additive.
- Do not commit.
