## Stack Guide

> **Stack-specific companion to [README.md](../README.md).** This file documents the concrete
> technologies, tools, and conventions of the reference implementation shipped with this template.
>
> The SDD pipeline itself (phases, gates, skills, contracts) is stack-agnostic. Everything in
> this file is replaceable when swapping stacks — future versions of this template will ship
> the pipeline core and stack overlays as separate packages.

---

## Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI, SQLAlchemy 2.0 async, Alembic, Pydantic v2, Python 3.13+ |
| Frontend | Nuxt 4, Vue 3.5+, TypeScript, Pinia, Tailwind CSS, pnpm |
| Database | PostgreSQL 18 |
| Cache | Redis 8 |
| Infra | Docker Compose, Nginx |
| CI | GitHub Actions |

---

## Prerequisites

```bash
docker --version        # Docker 24+
docker compose version  # v2+
uv --version            # any recent — https://docs.astral.sh/uv/getting-started/installation/
node --version          # 22+
pnpm --version          # 10+
```

> **`uv` is required for `./scripts/init-project.sh`.** The init script regenerates `uv.lock`
> after renaming the project in `pyproject.toml`; without it, `docker compose up --build`
> fails with `Missing workspace member`.

---

## Initial setup

After cloning and running `./scripts/init-project.sh`:

```bash
# 1. Review the generated environment
$EDITOR .env

# 2. Start the stack
docker compose up --build
# Backend:  http://localhost:8000
# Frontend: http://localhost:3000
```

`init-project.sh` already creates `.env`, injects fresh secrets, and rewrites template placeholders.
Migrations run automatically on backend startup. Hot-reload is active for both services —
changes in `app/` and `frontend/` are reflected immediately without restarting containers.

---

## Local IDE / git-hook setup (one-time)

These do not affect Docker — they set up your editor and git workflow.

```bash
# Python deps for IntelliSense / mypy
uv sync --dev
# VS Code: Ctrl+Shift+P → "Python: Select Interpreter" → .venv/bin/python

# Frontend deps for TS / Vue IntelliSense
cd frontend && pnpm install

# Pre-commit hooks (ruff lint + format on every commit)
uv run pre-commit install
```

---

## Default credentials

```
Email:    admin@example.com
Password: changeme123
```

Change these in [alembic/versions/0001_users_table.py](../alembic/versions/0001_users_table.py) before going to production.

---

## Gate Commands

This section is the authoritative command source for the phase-gate workflow. If the stack changes, update this table and keep the workflow wrappers untouched.

| Gate check | Command | Preconditions / notes |
|------------|---------|-----------------------|
| Infrastructure / bootstrap | `docker compose up -d` then `docker compose ps` | Use the repository `.env`. `db`, `redis`, `backend`, and `frontend` must be healthy; `nginx` must be running. |
| Migrations | `docker compose exec -T backend uv run alembic upgrade head` | Run inside the backend container so `.env`-backed credentials stay aligned. |
| Backend tests | `uv run pytest tests/ -v` | Run from the repo root. |
| Frontend type generation / prep | `cd frontend && pnpm nuxt prepare` | Required before frontend type-checks and Vitest when `.nuxt/` is missing or stale. |
| Frontend typecheck | `cd frontend && pnpm typecheck` | Depends on the prep step above. |
| Frontend unit tests | `cd frontend && pnpm test` | Depends on the prep step above. |
| E2E anti-flake lint | `cd frontend && pnpm test:e2e:lint` | Fails on committed `waitForTimeout(...)` usage in E2E specs. Debug-only waits must never be committed. |
| E2E (deterministic gate) | `cd frontend && pnpm test:e2e --project=chromium` | Run against the full Docker stack. Chromium is the only pass/fail browser for gate + PR CI. JUnit output should land at `frontend/test-results/junit.xml`; HTML report at `frontend/playwright-report/index.html`. |
| Smoke test | `curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/health` | Phase files may override the endpoint and expected result with a phase-specific smoke target. |

`./scripts/phase-gate.sh [XX]` is the preferred helper for this reference stack. It is an implementation of these gate commands, not a separate source of truth.

## Testing

### Backend (pytest)
SQLite in-memory by default. Set `DATABASE_URL` to run against Postgres (CI pattern).
```bash
uv run pytest
```

### Frontend unit / component (Vitest)
```bash
cd frontend && pnpm test
```

Nuxt-generated types are required for both type-checking and Vitest. If `.nuxt/` is missing
(common in CI or a fresh checkout), run:

```bash
cd frontend && pnpm nuxt prepare
```

### Frontend type-checking
```bash
cd frontend
pnpm nuxt prepare
pnpm typecheck
```

### Frontend end-to-end (Playwright)
E2E runs against the full Docker stack.
```bash
cd frontend
pnpm test:e2e:install   # first time only — downloads browsers
pnpm test:e2e:lint      # anti-flake policy check
pnpm test:e2e --project=chromium  # deterministic gate path
pnpm test:e2e:all                 # optional exploratory cross-browser run
```

Reports:
- CLI: `list` reporter (inline)
- HTML: `frontend/playwright-report/index.html`
- JUnit: `frontend/test-results/junit.xml` (parsed by `/phase-gate`)
- Traces: stored in `frontend/test-results/` for failed retries (`trace: on-first-retry`)

Determinism rules:
- Prefer `getByRole`, `getByLabel`, and `getByTestId` selectors.
- Use Playwright web-first assertions (`await expect(...)`) for readiness; do not use fixed sleeps.
- Use deterministic setup/fixtures with unique per-test data; never depend on leftovers from previous runs.
- Keep login behavior tests explicit, and use setup-storage state for post-auth flows.
- Add at least one E2E spec for each user-facing flow introduced in a phase.

### CI and branch protection

- CI includes a dedicated required job: `E2E (Chromium)` on pull requests.
- Configure branch protection in derived repositories so this job is required before merge.
- Keep the `CI` workflow as the single required PR path for Playwright in derived repositories (no duplicate standalone Playwright workflow unless intentionally non-gating).
- Use [E2E Pipeline Checklist](./E2E_PIPELINE_CHECKLIST.md) when setting up branch protection and pull-request templates.

### E2E troubleshooting

- Startup failures: inspect `docker compose ps` first; do not run Playwright until all services are healthy.
- Health-check drift: if `frontend` or `backend` checks fail, verify exposed ports and container health commands.
- Base URL mismatch: set `PLAYWRIGHT_BASE_URL` if running outside the default Docker URL.
- Auth-state corruption: delete `frontend/tests/e2e/.auth/` and rerun setup.
- Hydration race on SSR pages: fixture helpers should wait for app readiness (`html[data-app-ready="true"]`) before typing/clicking form controls.
- Artifact-first triage: inspect `frontend/playwright-report/index.html`, JUnit, and traces before changing assertions.

Full testing guidelines, including `data-testid` conventions and per-flow spec requirements, live in [../frontend/README.md](../frontend/README.md#testing).

---

## Project structure

```
.
├── .claude/skills/         # SDD pipeline skills (spec-sync, phase-init, phase-gate, context-update)
├── app/                    # FastAPI backend — see app/README.md
│   ├── api/v1/             # Routers grouped by resource
│   ├── core/               # config.py (Pydantic Settings), auth.py (JWT + role guards)
│   ├── db/                 # base.py, session.py, models/
│   └── schemas/            # Pydantic request/response models
├── alembic/                # DB migrations (autogenerated + hand-edited for seed / enum DDL)
├── frontend/               # Nuxt 4 app (Feature-Sliced Design) — see frontend/README.md
│   └── app/
│       ├── pages/          # Nuxt auto-routing
│       ├── layouts/        # App shell templates
│       ├── middleware/     # Route guards
│       ├── plugins/        # HTTP client init
│       ├── widgets/        # Composite UI blocks (auto-imported)
│       ├── features/       # User-facing feature slices
│       └── shared/         # api/, lib/, model/, types/ — zero business logic
├── tests/                  # pytest integration tests
├── docs/                   # SPEC, CONTEXT, STATE, CHANGELOG, PHASE_XX, STACK (this file)
├── docker-compose.yml
├── Dockerfile.backend
├── Dockerfile.frontend
├── nginx.conf
├── pyproject.toml
├── .env.example
└── AGENTS.md / CLAUDE.md   # AI agent rules (scope lock, gates, docs lookup, permission handoff)
```

---

## Per-module style guides

Before editing code under `app/` or `frontend/`, read the local style guide:

- Backend: [../app/README.md](../app/README.md) — ruff/mypy config, naming, key patterns (async session, role guards, Pydantic Settings)
- Frontend: [../frontend/README.md](../frontend/README.md) — FSD layers, auto-imports, Pinia conventions, E2E expectations

Both local guides repeat two load-bearing rules (docs lookup and permission-denied handoff) because an AI editing inside those subtrees often won't open the root [AGENTS.md](../AGENTS.md) or [CLAUDE.md](../CLAUDE.md).

---

## Common operations

### Add a new migration
```bash
uv run alembic revision --autogenerate -m "add_your_table"
uv run alembic upgrade head
```

### Stop everything
```bash
docker compose down       # stop containers, keep data
docker compose down -v    # stop containers + delete postgres volume
```

### Regenerate OpenAPI types for the frontend
```bash
cd frontend && pnpm generate:api
```
Overwrites `frontend/app/shared/types/schema.ts` from the backend OpenAPI spec.
