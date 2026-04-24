---
name: phase-gate
description: Run all gate checks for the current phase before committing. Checks docker infrastructure, pytest, Nuxt prepare, frontend type-checks, vitest, Playwright e2e, a smoke endpoint, and unresolved architect review notes. Reports PASS or FAIL.
allowed-tools: Bash, Read
argument-hint: "[phase number, e.g. 01]"
---

You are running the SDD `phase-gate` workflow.

**Target phase**: $ARGUMENTS

Execute the canonical playbook in [workflow/docs/playbooks/phase-gate.md](../../../workflow/docs/playbooks/phase-gate.md). Resolve the active gate helper/docs pair with `sdd gate resolve`; `docs/STACK.md#gate-commands` remains the human-readable command source. Do not duplicate their content here.

Read-only: do not edit code, do not commit.

If `$ARGUMENTS` is empty and `docs/STATE.md` has no `🔄 in-progress` phase, ask: "Which phase number should I check? (e.g. /phase-gate 01)"
