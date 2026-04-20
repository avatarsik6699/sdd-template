---
name: context-update
description: Update docs/CONTEXT.md after a phase is completed. Reads the phase Contracts section, bumps the version if schema/API/types changed, updates STATE.md and CHANGELOG.md.
allowed-tools: Read, Write, Edit, Glob
argument-hint: "[phase number, e.g. 01]"
---

> **Before generating code for any library (FastAPI, Nuxt, SQLAlchemy, Pydantic, etc.),
> follow the `ctx7` documentation-lookup rule in `CLAUDE.md`. Stale API knowledge is
> the #1 source of rework in this workflow.**

> Canonical portable playbook: `docs/workflows/context-update.md`

You are executing the SDD Context Update Protocol after a phase has been completed. Your job is to synchronize `docs/CONTEXT.md`, `docs/STATE.md`, and `docs/CHANGELOG.md` with the reality of what was built.

**Target phase**: $ARGUMENTS

## Step 1 — Read all relevant files

Read these files before making any edits:
- `docs/PHASE_$ARGUMENTS.md` — focus on the **Contracts** section
- `docs/CONTEXT.md` — current contract (note the `_meta.version` value)
- `docs/STATE.md` — current phase statuses
- `docs/CHANGELOG.md` — recent history

## Step 2 — Confirm phase is ready

Check `docs/STATE.md`:
- If the phase is `⏳ pending`: warn "Phase $ARGUMENTS has not started yet. Are you sure gate checks passed?" and wait for confirmation before proceeding.
- If the phase is `✅ done`: warn "Phase $ARGUMENTS is already marked done. Re-running will overwrite — confirm?" and wait.
- If `🔄 in-progress` or gate checks just passed: proceed.

## Step 3 — Extract contracts from the phase file

From the **Contracts** section of `docs/PHASE_$ARGUMENTS.md`, extract:
- New DB tables / columns (from "New DB tables / columns")
- New API endpoints (from "New API endpoints" table)
- New TypeScript types / Pinia stores (from "New TypeScript types" block)
- New env vars (from "New env vars" table — key names only)

If the Contracts section is missing or says "None" for all items: no version bump needed. Skip to Step 6.

## Step 4 — Determine version bump

Apply these rules to the `_meta.version` in `docs/CONTEXT.md`:

- **No bump**: all Contracts sections say "None" (docs-only phase)
- **Patch bump** (e.g., `v1.0` → `v1.1`): any new tables, endpoints, types, or env vars added (additive only, nothing removed or renamed)
- **Minor bump** (e.g., `v1.1` → `v1.2`): breaking changes — renamed endpoints, removed fields, changed request/response shape, column type changes

State clearly which bump applies and why before editing.

## Step 5 — Update docs/CONTEXT.md

Make surgical edits:

1. Increment `_meta.version` (if bump needed)
2. Update `captured_at` to today's date (format: `YYYY-MM-DD`)
3. Update `phase_completed` to the phase number (e.g., `"01"`)
4. Update `phase_in_progress` to the next phase number or `null`
5. **Append** new entries to `core_models` array — do NOT remove existing
6. **Append** new entries to `endpoints_active` array — do NOT remove existing
7. **Append** new table names to `db_schema.tables` array
8. Update `db_schema.current_head` to the latest alembic revision name
9. **Append** new key names to `env_config.keys` array
10. Update `notes` with one sentence: "Phase XX complete. [What was added]."

## Step 6 — Add entry to docs/CHANGELOG.md (if version bumped)

If CONTEXT.md version was bumped, add a new entry at the very top of `docs/CHANGELOG.md` (immediately after the `# CHANGELOG` heading and description lines, before the previous top entry).

Use this format:
```
## [new version] — [YYYY-MM-DD] — Phase [XX] complete

**Type**: phase-completion
**Author**: AI (context-update skill)
**Triggered by**: PHASE_[XX] gate passed and committed

### Changes
- [list what was built / added]

### Affected Phases
- None (additive change)

### Contract Updates
- `CONTEXT.md` bumped from `vX.Y` to `vX.Z`
- [list: new tables, new endpoints, new env vars]

### Notes
[Any notable decisions made during this phase]
```

If version was NOT bumped: do not add a CHANGELOG entry.

## Step 7 — Update docs/STATE.md

1. Change the PHASE_[XX] row status from current status to `✅ done`
2. Change Gate column from `⬜` to `✅`
3. Add an entry to the Change Log table: `| [YYYY-MM-DD] | PHASE_[XX] completed — CONTEXT.md bumped to vX.Z |`

## Step 8 — Report

Output a summary:

```
## context-update complete — PHASE_[XX]

- CONTEXT.md: bumped from vX.Y to vX.Z / no version change — [reason]
- STATE.md: PHASE_[XX] marked ✅ done
- CHANGELOG.md: entry added / no entry needed

Next step: /phase-init [XX+1] to scaffold the next phase
```

## Rules
- Never remove existing entries from CONTEXT.md arrays — only append
- If the phase Contracts section is incomplete, ask the user to fill it in before proceeding
- Do not commit — the human reviews and commits
- The `_meta.version` in CONTEXT.md is the single source of truth; CHANGELOG.md entries derive from it
