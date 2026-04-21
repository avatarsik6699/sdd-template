---
name: phase-gate
description: Run all gate checks for the current phase before committing. Checks docker infrastructure, pytest, Nuxt prepare, frontend type-checks, vitest, Playwright e2e, a smoke endpoint, and unresolved architect review notes. Reports PASS or FAIL.
allowed-tools: Bash, Read
argument-hint: "[phase number, e.g. 01]"
---

You are running the SDD `phase-gate` workflow.

**Target phase**: $ARGUMENTS

Execute the canonical playbook in [docs/workflows/phase-gate.md](../../../docs/workflows/phase-gate.md). Stack-specific commands are dispatched from [docs/STACK.md → Gate Commands](../../../docs/STACK.md#gate-commands). Both files are the source of truth — do not duplicate their content here.

Read-only: do not edit code, do not commit.

If `$ARGUMENTS` is empty and `docs/STATE.md` has no `🔄 in-progress` phase, ask: "Which phase number should I check? (e.g. /phase-gate 01)"
