> **TEMPLATE FILE** — Copy this file to the root of a new project as `AGENTS.md`.
> Replace `[PROJECT_NAME]` with the actual project name.
> This is the canonical, model-agnostic rules file. The project's `CLAUDE.md` is a thin wrapper that points here.

---

# Rules of operation of the AI agent during [PROJECT_NAME] development

## Core Rules

1. **Scope Lock**: Do only what is specified in the active `docs/PHASE_XX.md`. Do not assume future phases.
2. **No Guessing**: If a requirement is genuinely ambiguous and risky, ask a concise terminal question instead of inventing behavior.
3. **Gates First**: Before each commit, run the `phase-gate` workflow for the current phase. Commit only if the report is PASS. Automated green is not enough if `Architect Review Notes` still has unchecked items.
4. **Atomic Commits**: `feat|fix|chore|docs|test|refactor(scope): description`. One commit = one logical task.
5. **Security**: No hardcoded secrets. Use `.env`, environment variables, and typed settings (e.g. Pydantic Settings).
6. **Context Sync**: After each phase completes, run the `context-update` workflow to refresh `docs/CONTEXT.md`, `docs/STATE.md`, and `docs/CHANGELOG.md`.
7. **E2E First**: For every user-facing feature touched in a phase, add or update a Playwright spec under `frontend/tests/e2e/`. Chromium is the canonical pass/fail browser for phase gates and PR CI in the reference stack.
8. **Output Discipline**: First the plan → wait for architect `✅` → code → tests → commit. Do not skip steps.

## Stack Conventions

Before writing code, running commands, or reasoning about project layout, read **[docs/STACK.md](../docs/STACK.md)**. It is the single source of truth for this project's concrete technologies, directory structure, setup commands, test tooling, and per-module style guides. When a user question depends on stack specifics (test commands, file locations, migration tool), consult `STACK.md` first.

## Library Documentation Lookup

Before writing or reviewing code that uses any external library, framework, SDK, CLI tool, or cloud service (FastAPI, SQLAlchemy, Pydantic, Alembic, httpx, Typer, Nuxt, Vue, Pinia, Vite, Tailwind, Nuxt UI, Vitest, Playwright, etc.), consult up-to-date documentation in this preference order:

1. `Context7` via MCP, if the runtime exposes it
2. For OpenAI products specifically, the official OpenAI developer docs MCP server
3. `ctx7` CLI: `npx ctx7@latest library "<name>"` then `npx ctx7@latest docs /org/project "<question>"`
4. Official library docs / primary-source API references

Rules:

- Use the official library name with correct punctuation (`Next.js`, not `nextjs`).
- Do NOT rely on training-data knowledge alone — library APIs drift between minor versions.
- Skip only for: pure refactoring, business-logic debugging, code review of existing code, or general programming concepts not tied to a specific library.
- Cap at 3 `ctx7` calls per question. If unclear, ask the user rather than guessing.
- Never include secrets (API keys, passwords) in queries.
- If quota or auth fails, suggest `npx ctx7@latest login` or setting `CONTEXT7_API_KEY`.

Stale library knowledge is the #1 source of rework. Treat documentation lookup as required, not optional.

## Repo Memory Files

Keep lightweight long-lived project memory in `docs/` so future sessions recover context without reconstructing it from chat history:

- `docs/DECISIONS.md` — ADR-style technical decisions
- `docs/KNOWN_GOTCHAS.md` — recurring pitfalls, symptoms, and fixes

Consult and update these files as part of normal development. Keep them concise and current.

## Filesystem Permission Failures

On `EACCES`, `EPERM`, "Permission denied", or "Read-only file system" (most often after a Docker run leaves `.nuxt/`, `.output/`, or `node_modules/.cache/` root-owned on the host): **stop immediately**. Do NOT `sudo`, `chmod -R 777`, delete-and-recreate the file elsewhere, or silently skip the step.

Post the exact handoff message from [docs/KNOWN_GOTCHAS.md § Docker-owned files](../docs/KNOWN_GOTCHAS.md#docker-owned-files-break-host-operations-eacces--eperm--read-only) to the user with the real `<path>` and `<cmd>`, then wait. On the keyword `continue`, retry the failed operation once. If it fails a second time with the same error, stop again and ask the user to confirm the fix — do not loop a third time.

## Git Workflow

1. **Branch Rule**: Work only in `feat/phase-N` branches. Never push directly to `main` or `develop`.
   ```bash
   git checkout -b feat/phase-01
   ```
2. **No Destructive Git**: Never use `--force`, `git push --force`, `git rebase` on shared branches, or `git reset --hard` without explicit user instruction.
3. **Conventional Commits**: `type(scope): description`, types: `feat`, `fix`, `chore`, `docs`, `test`, `refactor`.
   Example: `feat(phase-01): foundation — docker, db, jwt auth, nuxt skeleton`.
4. **Gate Before Commit**: Run the `phase-gate` workflow first. Never commit on ❌ FAIL.
5. **Tagging**: After a phase branch merges to `develop`:
   ```bash
   git tag -a v0.N.0 -m "Phase N: [title]"
   ```

## Playwright Determinism Rules

1. Prefer `getByRole`, `getByLabel`, and `getByTestId` selectors over CSS selectors.
2. Use Playwright web-first assertions (`await expect(...)`) for readiness and state transitions.
3. Do not use `waitForTimeout` in committed tests except temporary local debugging.
4. Keep login-flow tests explicit; use setup-generated `storageState` for post-auth scenarios.
5. Ensure test data is deterministic: unique per worker/test and independent from previous runs.
6. For the reference stack gate and PR CI, run:
   ```bash
   pnpm test:e2e:lint
   pnpm test:e2e --project=chromium
   ```
   Cross-browser runs are optional and non-gating unless the project explicitly tightens policy.
7. Keep branch protection aligned with [docs/E2E_PIPELINE_CHECKLIST.md](../docs/E2E_PIPELINE_CHECKLIST.md), including required check name `E2E (Chromium)` from the `CI` workflow.

## Spec Change Sync Protocol

When `docs/SPEC.md` is modified:

1. **Run immediately**: the `spec-sync` workflow with a brief description of what changed.
2. It will: add a `docs/CHANGELOG.md` entry, increment `docs/CONTEXT.md` `_meta.version` if DB/API/types changed, mark affected phases as `⚠️ NEEDS_REVIEW` in `docs/STATE.md`, and add warning banners to affected `docs/PHASE_XX.md` files.
3. **Review** all changes before committing.
4. **Do not implement** any phase marked `⚠️ NEEDS_REVIEW` until resolved.

## CONTEXT.md Version Rules

- **Format**: `vMAJOR.MINOR` (e.g. `v1.2`).
- **Patch bump** (`v1.0` → `v1.1`): additive only — new endpoints, models, env vars.
- **Minor bump** (`v1.1` → `v1.2`): breaking — renamed/removed endpoints, schema or type changes.
- **No bump**: docs-only phase, zero contract changes.
- Always update `captured_at` when the version changes.
- `CONTEXT.md` is the Single Source of Truth for AI — never let it fall more than one phase behind.

## Workflow Playbooks

The four SDD workflows are defined in `docs/workflows/`:

- [`phase-init`](../docs/workflows/phase-init.md) — scaffold a new `docs/PHASE_XX.md`
- [`phase-gate`](../docs/workflows/phase-gate.md) — validate a phase before commit (stack commands in [docs/STACK.md](../docs/STACK.md#gate-commands))
- [`spec-sync`](../docs/workflows/spec-sync.md) — propagate a `docs/SPEC.md` change
- [`context-update`](../docs/workflows/context-update.md) — finalize a completed phase

Different runtimes expose them differently:

- **Claude Code**: slash commands (`/phase-init`, `/phase-gate`, `/spec-sync`, `/context-update`) defined under `.claude/skills/`.
- **Codex**: slash commands defined under `plugins/sdd-workflow/`.
- **Other runtimes**: follow the markdown procedure in `docs/workflows/` manually.

The runtime wrappers are thin stubs — all workflow logic lives in `docs/workflows/`.

## Phase Lifecycle

```
1.  Architect fills docs/SPEC.md
2.  phase-init N      → creates docs/PHASE_N.md scaffold
3.  Architect fills Contracts + Files sections
4.  AI implements scope on feat/phase-N branch
5.  phase-gate N      → automated baseline
6.  Architect manual verification → add unchecked items to Architect Review Notes
7.  phase-gate N      → ✅ PASS only when all automated checks green AND review notes all checked off
8.  git commit        → feat(phase-N): [description]
9.  context-update N  → updates CONTEXT, STATE, CHANGELOG
10. PR to develop     → human review → merge
11. git tag -a v0.N.0 -m "Phase N: [title]"
12. phase-init N+1    → repeat
```

## Document Roles

| File | Role | Change cadence |
|------|------|----------------|
| `docs/SPEC.md` | Strategic brief: goals, roles, domain rules, non-functional reqs | Rarely — architect only |
| `docs/CONTEXT.md` | Living technical contract: DB schema, endpoints, TS types, env vars | After each phase via `context-update` |
| `docs/STATE.md` | Operational tracker: phase statuses, blockers, feedback | Continuously |
| `docs/CHANGELOG.md` | History of spec/architecture changes | On every SPEC.md or CONTEXT.md change |
| `docs/PHASE_XX.md` | Mini-spec for AI: scope, files, contracts, gate checks | Created per phase via `phase-init` |
| `docs/STACK.md` | Stack-specific setup, commands, layout, Gate Commands dispatch | When the stack changes |
| `docs/DECISIONS.md` | ADR log | On each architecturally meaningful decision |
| `docs/KNOWN_GOTCHAS.md` | Recurring pitfall log | When a new trap is discovered |
