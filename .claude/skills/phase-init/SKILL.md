---
name: phase-init
description: Scaffold a new PHASE_XX.md from PHASE_TEMPLATE.md. Fills metadata, links to current CONTEXT.md version, adds scope from SPEC.md Section 8, and adds the phase row to STATE.md.
allowed-tools: Read, Write, Glob
argument-hint: "[phase number, e.g. 02]"
---

You are initializing a new phase document for the SDD workflow.

**Target phase**: $ARGUMENTS

## Step 1 — Validate input

- If no argument provided: respond with "Which phase number? Usage: /phase-init 02"
- Normalize to 2 digits: "2" → "02", "10" → "10", "3" → "03"
- Check whether `docs/PHASE_$ARGUMENTS.md` already exists (use Glob or Read).
  If it exists: warn "docs/PHASE_XX.md already exists. Proceeding will overwrite it. Confirm?"
  Wait for user confirmation before continuing.

## Step 2 — Read context

Read these files:
- `docs/PHASE_TEMPLATE.md` — template to copy
- `docs/CONTEXT.md` — get current `_meta.version` and `phase_completed`
- `docs/STATE.md` — find the previous phase status
- `docs/SPEC.md` — Section 8 (phases plan) to find this phase's scope

## Step 3 — Confirm previous phase is complete

Find PHASE_[XX-1] in STATE.md (where XX-1 is the previous phase number, e.g. if creating PHASE_03, check PHASE_02).

- If previous phase is `✅ done`: proceed.
- If previous phase is anything else: warn "PHASE_[XX-1] is not marked ✅ done (current status: [status]). Starting the next phase before completing the previous one may cause context drift. Proceed anyway?"
- Wait for confirmation if warning triggered.
- If creating PHASE_01 (no previous): skip this check.

## Step 4 — Extract scope from SPEC.md

Look in SPEC.md Section 8 for this phase number ("Phase [N]:", "Phase [NN]:", "Фаза [N]:", etc.).

Extract:
- Phase title
- Scope items listed under Backend
- Scope items listed under Frontend
- Gate requirements

If this phase is not defined in SPEC.md Section 8:
- Set title to "[TODO: Fill in phase title]"
- Set scope to placeholder checkboxes with `[TODO: define scope]`
- Add a warning at the top of the created file

## Step 5 — Create docs/PHASE_XX.md

Copy the structure from PHASE_TEMPLATE.md and substitute:

| Placeholder | Value |
|-------------|-------|
| `[XX]` | Zero-padded phase number (e.g. `02`) |
| `[Phase Title]` | Title from SPEC.md Section 8 (or "[TODO: Fill in]") |
| `v0.[XX].0` | Correct tag (phase 2 → `v0.2.0`, phase 10 → `v0.10.0`) |
| `PHASE_[XX-1]` | Actual previous phase (e.g. `PHASE_01`) |
| `[VERSION — snapshot...]` | Current `_meta.version` from CONTEXT.md (e.g. `v1.1`) |
| Scope checkboxes | Paste Backend/Frontend items from SPEC.md Section 8 as `- [ ] [item]` |

Leave these sections with `[TODO: ...]` placeholders for the architect:
- Files — create / modify
- Contracts — DB tables, endpoints, TS types, env vars (all four subsections)
- Gate Checks smoke test URL and expected response
- Atomic Commit Message description part

Do NOT invent contract details. Only fill in what is clearly defined in SPEC.md.

## Step 6 — Add phase row to docs/STATE.md

Append a new row to the "Phase Status" table:
```
| PHASE_[XX] | ⏳ pending | v0.[XX].0 | ⬜ | - | [Phase Title] |
```

Place it after the last existing row in the table.

## Step 7 — Report

Output:
```
## phase-init complete

Created: docs/PHASE_[XX].md
STATE.md: PHASE_[XX] row added (⏳ pending)

Before handing to AI for implementation, the architect must fill in:
1. "Files — Create / modify" section
2. "Contracts" section — DB tables, API endpoints, TS types, env vars
3. Gate Checks — smoke test URL and expected response
4. Atomic Commit Message — description

CONTEXT.md version at time of init: [version]
```

## Rules
- Never modify `docs/SPEC.md`
- Never modify `docs/CONTEXT.md`
- The created file is a **DRAFT** — architect must complete Contracts + Files before AI implements
- Use `[TODO: ...]` markers clearly so nothing is silently missing
- Do not commit
