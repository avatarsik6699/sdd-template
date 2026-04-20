---
name: spec-sync
description: Propagate SPEC.md changes into the rest of the SDD documentation set. Use when the system spec has changed and downstream contracts may now be stale.
metadata:
  priority: 5
  pathPatterns:
    - 'docs/SPEC.md'
    - 'docs/CONTEXT.md'
    - 'docs/STATE.md'
    - 'docs/CHANGELOG.md'
    - 'docs/PHASE_*.md'
  promptSignals:
    phrases:
      - "spec sync"
      - "sync after spec change"
      - "spec changed"
      - "prevent context drift"
    allOf:
      - [spec, sync]
      - [spec, changed]
    anyOf:
      - "context drift"
      - "phase review"
      - "contract update"
    noneOf: []
    minScore: 6
retrieval:
  aliases:
    - sync spec change
    - update phases after spec edit
  intents:
    - propagate a spec change
    - mark affected phases for review
  entities:
    - SPEC.md
    - CONTEXT.md
    - PHASE files
---

# spec-sync

Canonical portable playbook: `docs/workflows/spec-sync.md`

Use this skill after `docs/SPEC.md` changes, especially when the change may affect contracts, gates, or phase sequencing.

Workflow:

1. Read `docs/SPEC.md`, `docs/CONTEXT.md`, `docs/STATE.md`, `docs/CHANGELOG.md`, and all `docs/PHASE_*.md`.
2. Inspect the recent diff and the user-provided description of what changed.
3. Determine impacted domains and phases.
4. Add a top-level `docs/CHANGELOG.md` entry.
5. Update `docs/CONTEXT.md` only when the technical contract changed.
6. Mark affected phases as `NEEDS_REVIEW` in `docs/STATE.md`.
7. Patch the affected phase files surgically.
8. Report what changed, what needs review, and what is still unaffected.

Rules:

- Never rewrite a phase file from scratch.
- Prefer false positives over missed downstream dependencies.
- Do not commit.
