---
name: spec-sync
description: Run when docs/SPEC.md has changed. Propagates the change to CHANGELOG.md, STATE.md, CONTEXT.md, and affected PHASE_XX.md files following the SDD sync protocol. Prevents context drift.
allowed-tools: Read, Write, Edit, Glob, Bash
argument-hint: "[brief description of what changed in SPEC.md]"
---

> **Before generating code for any library (FastAPI, Nuxt, SQLAlchemy, Pydantic, etc.),
> follow the `ctx7` documentation-lookup rule in `CLAUDE.md`. Stale API knowledge is
> the #1 source of rework in this workflow.**

> Canonical portable playbook: `docs/workflows/spec-sync.md`

You are executing the SDD Spec Change Sync Protocol.

`docs/SPEC.md` has been modified. Your job is to propagate that change correctly across all documents without losing any existing data.

**Change description**: $ARGUMENTS

**Recent SPEC.md git history**:
!`git log --oneline -5 -- docs/SPEC.md 2>/dev/null || echo "git log unavailable"`

**SPEC.md diff (uncommitted or last commit)**:
!`git diff HEAD -- docs/SPEC.md 2>/dev/null || git diff HEAD~1 HEAD -- docs/SPEC.md 2>/dev/null || echo "No diff available — SPEC.md may already be committed"`

---

## Step 1 — Read current state

Read these files in full before making any edits:
- `docs/SPEC.md` (the updated spec)
- `docs/CONTEXT.md` (current contract — note `_meta.version`)
- `docs/STATE.md` (current phase statuses)
- `docs/CHANGELOG.md` (history)
- All `docs/PHASE_*.md` files (use Glob pattern `docs/PHASE_*.md`)

## Step 2 — Impact Analysis

Determine which domains changed in SPEC.md by examining the diff and the `$ARGUMENTS` description:

| Domain | Signal | Affects |
|--------|--------|---------|
| **Data model** (Section 3) | table renamed, column added/removed/typed | CONTEXT.md `core_models` / `db_schema`, PHASE_XX.md files touching those tables |
| **API endpoints** (Section 4.2) | endpoint added/renamed/removed | CONTEXT.md `endpoints_active`, PHASE_XX.md files implementing those routes |
| **Frontend** (Section 5) | pages/stores/components changed | PHASE_XX.md files building those components |
| **Non-functional reqs** (Section 7) | performance, security, coverage | Gate checks in affected PHASE_XX.md files |
| **Phase plan** (Section 8) | phase reordered, scope changed | The specific PHASE_XX.md files and STATE.md ordering |

For each changed domain, list the affected PHASE_XX.md files and the precise reason.

**False-positive rule**: if you are unsure whether a phase is affected, mark it `⚠️ NEEDS_REVIEW`. A false positive is safer than a missed dependency.

## Step 3 — Update docs/CHANGELOG.md

Determine the new CONTEXT.md version:
- If DB/API/types changed (additive): patch bump (e.g., `v1.1` → `v1.2`)
- If DB/API/types changed (breaking — renamed/removed): minor bump (e.g., `v1.2` → `v2.0`)
- If no contract change (docs-only, non-functional reqs only): no version bump; use current version in the entry heading

Add a new entry at the **very top** of `docs/CHANGELOG.md` — immediately after the `# CHANGELOG` heading and its description lines, before any previous entry.

```markdown
## [new or current CONTEXT version] — [YYYY-MM-DD] — [Short Title]

**Type**: spec-change
**Author**: AI (spec-sync skill)
**Triggered by**: [use $ARGUMENTS; describe what changed in SPEC.md]

### Changes
- [bullet: specific section and what changed]

### Affected Phases
- PHASE_XX — [precise reason]
- (or: None — change has no impact on existing phases)

### Contract Updates
- `CONTEXT.md` bumped from `vX.Y` to `vX.Z` (if applicable)
- [list: renamed endpoints, new tables, etc.]
- (or: No contract change — docs-only update)

### Notes
[Any relevant trade-offs, decisions, or context]
```

## Step 4 — Update docs/CONTEXT.md (only if contract changed)

Update CONTEXT.md **only if** the change affects the technical contract (DB schema, API endpoints, TS types, env vars, stack).

If update needed:
1. Increment `_meta.version` (patch or minor as determined in Step 3)
2. Update `captured_at` to today's date (`YYYY-MM-DD`)
3. Update only the specific sections that changed:
   - `core_models`: update if data model changed (do NOT remove existing entries unless spec explicitly removes them)
   - `endpoints_active`: update if endpoints changed
   - `db_schema.tables`: update if tables added/removed
   - `env_config.keys`: update if env vars added
4. Update `notes` with one sentence about the spec change

If NO contract change: do not modify CONTEXT.md. Note "no contract change" in the CHANGELOG entry.

## Step 5 — Mark affected phases in docs/STATE.md

For each PHASE_XX.md identified as affected in Step 2:

1. Find the phase row in the Phase Status table
2. Change its status to `⚠️ NEEDS_REVIEW`
3. Add an entry to the Active Blockers section:
   ```
   PHASE_XX [YYYY-MM-DD]: needs review after spec change — [brief reason]. Resolve before implementing.
   ```

Do NOT change phases already marked `✅ done` unless their specific contracts are directly broken by the spec change (e.g., an endpoint they implemented was renamed).

## Step 6 — Patch affected PHASE_XX.md files

For each affected phase file:

1. Add a warning banner immediately after the Phase Metadata table (before the Phase Goal section):
   ```markdown
   > ⚠️ **NEEDS_REVIEW** — Spec changed on [YYYY-MM-DD].
   > Check [specific section, e.g., "Section 3 data model"] against updated `docs/SPEC.md`.
   > Re-validate the **Contracts** section before implementation.
   ```

2. If the change is clear-cut and unambiguous (e.g., an endpoint was renamed from `/users` to `/api/v1/users`), apply the surgical edit to the Contracts section.

3. Do NOT rewrite the phase file. Surgical edits only. Preserve all existing content.

## Step 7 — Verify and report

After all edits, output a sync report:

```
## spec-sync complete

**CHANGELOG.md**: new entry added (v[old] → v[new] / no version bump)
**CONTEXT.md**: [bumped to vX.Z / not changed] — [reason]
**STATE.md phases marked ⚠️ NEEDS_REVIEW**: [PHASE_XX, PHASE_YY / none]
**PHASE files patched**: [PHASE_XX, PHASE_YY / none]
**Unaffected phases**: [PHASE_XX / none]

Next steps:
1. Review these changes before committing
2. Resolve each NEEDS_REVIEW phase: update its Contracts section if needed, then remove the ⚠️ banner
3. Do not implement any NEEDS_REVIEW phase until resolved
```

## Rules
- Never delete existing CHANGELOG.md entries
- Never remove endpoints/models from CONTEXT.md unless spec explicitly removes them
- Never rewrite a PHASE_XX.md from scratch — surgical edits only
- Do not commit — the human reviews and commits after inspecting changes
- If $ARGUMENTS is empty and no diff is available: ask "What changed in SPEC.md? Please describe so I can assess impact accurately."
