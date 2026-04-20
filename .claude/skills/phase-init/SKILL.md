---
name: phase-init
description: Scaffold a new PHASE_XX.md from PHASE_TEMPLATE.md. Fills metadata, scope, Contracts, and Files by extracting data from SPEC.md. Adds the phase row to STATE.md.
allowed-tools: Read, Write, Glob
argument-hint: "[phase number, e.g. 02]"
---

> **Before generating code for any library (FastAPI, Nuxt, SQLAlchemy, Pydantic, etc.),
> follow the `ctx7` documentation-lookup rule in `CLAUDE.md`. Stale API knowledge is
> the #1 source of rework in this workflow.**

> Canonical portable playbook: `docs/workflows/phase-init.md`

You are initializing a new phase document for the SDD workflow.

**Target phase**: $ARGUMENTS

## Step 1 — Validate input

- If no argument provided: respond with "Which phase number? Usage: /phase-init 02"
- Normalize to 2 digits: "2" → "02", "10" → "10", "3" → "03"
- Check whether `docs/PHASE_$ARGUMENTS.md` already exists (use Glob or Read).
  If it exists: warn "docs/PHASE_XX.md already exists. Proceeding will overwrite it. Confirm?"
  Wait for user confirmation before continuing.

## Step 2 — Read context

Read these files in full:
- `docs/PHASE_TEMPLATE.md` — template to copy
- `docs/CONTEXT.md` — get current `_meta.version` and `phase_completed`
- `docs/STATE.md` — find the previous phase status
- `docs/SPEC.md` — read ALL sections: §3 (data model), §4.1 (architecture), §4.2 (endpoints), §4.3 (code requirements), §5 (frontend pages, components, stores), §6 (infrastructure), §8 (phases plan)

## Step 3 — Confirm previous phase is complete

Find PHASE_[XX-1] in STATE.md (where XX-1 is the previous phase number).

- If previous phase is `✅ done`: proceed.
- If previous phase is anything else: warn "PHASE_[XX-1] is not marked ✅ done (current status: [status]). Starting the next phase before completing the previous one may cause context drift. Proceed anyway?"
- Wait for confirmation if warning triggered.
- If creating PHASE_01 (no previous): skip this check.

## Step 4 — Extract scope AND contracts from SPEC.md

### 4a. Scope from §8

Find this phase in SPEC.md Section 8. Extract:
- Phase title
- All scope items (Backend, Frontend, Gate)

If this phase is not in §8:
- Set title to "[TODO: Fill in phase title]"
- Set scope to `- [ ] [TODO: define scope]`
- Add a warning at top of the created file

### 4b. DB tables (from §3)

Read the full data model in §3. Identify which tables are **first introduced** in this phase by matching table names to the scope description in §8:
- Example: Phase 1 scope mentions "users table" → extract the `users(...)` block from §3
- Include ONLY tables introduced in this specific phase (not tables from prior phases)
- Paste the exact table definition blocks verbatim from §3
- If no new tables in this phase: write `— no new tables in this phase`

### 4c. API endpoints (from §4.2)

Read the endpoint table in §4.2. Select rows that belong to this phase:
- Match by what entities/resources the scope mentions
- Example: Phase 1 mentions "JWT auth (login, me, logout)" and "health" → extract those 4 rows
- Include the full row: Method | Path | Auth | Description
- If no new endpoints: write `— no new endpoints in this phase`

### 4d. TypeScript types and Pinia stores (infer from §3 + §5)

For each new table introduced in this phase, derive the corresponding Pydantic → TypeScript type:
- Map snake_case columns to camelCase TypeScript fields
- UUID → `string`, VARCHAR → `string`, BOOLEAN → `boolean`, INT/NUMERIC → `number`, TIMESTAMPTZ → `string` (ISO), JSONB → typed or `Record<string, unknown>`
- Omit `hashed_password` from UserOut; include only fields safe to expose to the client
- Generate a `[EntityName]Out` type (what the API returns) and request types as needed (e.g. `LoginRequest`, `TokenResponse`)
- From §5.2, identify which Pinia stores are first set up in this phase. List each store name and the state fields/actions it will expose.
- If no new types or stores: write `— no new types/stores in this phase`

### 4e. Files (from §4.1 + §5.1 + §5.2 + §6)

Build the explicit file list by mapping the scope to the architecture defined in SPEC.md:

**Backend files** — read §4.1 architecture tree; include only the files needed by this phase's scope:
- `app/api/v1/*.py` routes introduced in this phase
- `app/db/models/*.py` for new tables
- `app/schemas/*.py` for new Pydantic schemas
- `app/core/*.py` if touched (config, auth)
- `db/alembic/versions/XXXX_*.py` for new migrations
- `pyproject.toml`, `uv.lock` if dependencies change

**Frontend files** — read §5.1 pages and §5.2 stores/components; include only what this phase introduces:
- `pages/*.vue`, `pages/**/*.vue` for new pages
- `stores/*.ts` for new Pinia stores
- `composables/*.ts` for new composables
- `components/**/*.vue` for new components

**Infrastructure files** — read §6; include if touched in this phase:
- `docker-compose.yml`
- `Dockerfile.backend`, `Dockerfile.frontend`
- `nginx/nginx.conf`
- `.github/workflows/*.yml`
- `.env.example`

Format as a flat list of relative paths from repo root.

### 4f. Environment variables

From the scope and the stack config, list env vars needed **for the first time** in this phase:
- Map to example values and whether they're required
- Draw from §4.3 (Pydantic Settings), docker-compose service configs, and JWT/auth requirements
- If no new env vars: write `— no new env vars in this phase`

## Step 5 — Create docs/PHASE_XX.md

Copy the structure from PHASE_TEMPLATE.md and substitute all placeholders:

| Placeholder | Value |
|-------------|-------|
| `[XX]` | Zero-padded phase number |
| `[Phase Title]` | Title from §8 |
| `v0.[XX].0` | Correct tag |
| `PHASE_[XX-1]` | Actual previous phase |
| `[VERSION]` | Current `_meta.version` from CONTEXT.md |
| Scope checkboxes | Items from §8 as `- [ ] [item]` |
| Files section | Explicit file list from Step 4e |
| Contracts — DB tables | Table definitions from Step 4b |
| Contracts — API endpoints | Endpoint rows from Step 4c |
| Contracts — TS types/stores | Types and stores from Step 4d |
| Contracts — Env vars | Env var table from Step 4f |
| Atomic Commit Message | Generated from phase number + scope (see rule below) |

**Rules for filling Contracts:**
- Extract verbatim from SPEC.md wherever possible — do not paraphrase
- Use `[TODO: verify]` only when a specific detail cannot be derived from SPEC.md (e.g. a concrete example value for an env var)
- Do NOT leave entire sections blank or as generic `[TODO: ...]` — always make a best-effort extraction
- Do NOT invent data that isn't in SPEC.md

**Rule for Atomic Commit Message:**
Derive the description from the phase title and 2–4 key deliverables extracted from the scope in Step 4a.
Format: `feat(phase-[XX]): [phase title in lowercase] — [key deliverable 1], [key deliverable 2], ...`
Keep the total line under 72 characters. Focus on WHAT was built, not HOW.
Example: `feat(phase-02): user management — doctor/patient profiles, admin CRUD, RBAC guards`

Leave as `[TODO: verify]` only:
- Gate Checks smoke test expected response body (if not obvious)

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

Contracts filled from SPEC.md:
- DB tables: [list table names, or "none"]
- Endpoints: [count] rows
- TS types: [list type names, or "none"]
- Pinia stores: [list store names, or "none"]
- Env vars: [count] vars
- Files: [count] files listed

Before handing to AI for implementation, verify:
1. Gate Checks — confirm smoke test expected response if left as [TODO: verify]
2. Any [TODO: verify] markers in Contracts

CONTEXT.md version at time of init: [version]
```

## Rules
- Never modify `docs/SPEC.md`
- Never modify `docs/CONTEXT.md`
- Extract contracts from SPEC.md — do not invent or leave blank
- Use `[TODO: verify]` sparingly and only when data is genuinely absent from SPEC.md
- Do not commit
