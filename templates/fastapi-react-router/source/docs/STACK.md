## Stack Guide

> Stack-specific companion to the workflow docs. The SDD workflow remains stack-agnostic; this file
> records the concrete commands and layout for the FastAPI + React Router SSR template.

---

## Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI, SQLAlchemy 2.0 async, Alembic, Pydantic v2, Python 3.13+ |
| Frontend | React 19, React Router 7 framework mode, Vite, TypeScript, pnpm |
| Database | PostgreSQL 18 |
| Cache | Redis 8 |
| Infra | Docker Compose, Nginx |
| CI | GitHub Actions |

---

## Prerequisites

```bash
docker --version
docker compose version
uv --version
node --version
pnpm --version
```

---

## Initial setup

After running `uv run sdd init --template fastapi-react-router --project-name <slug> <target-dir>`
and then `./scripts/init-project.sh` inside the generated project:

```bash
$EDITOR .env
docker compose up --build
```

Default local endpoints:

- Backend API: `http://localhost:8000`
- Frontend SSR app: `http://localhost:3000`

---

## Gate Commands

This section is the human-readable command source for the phase-gate workflow. The machine-readable
dispatch lives in `.sdd/template-manifest.yaml`.

| Gate check | Command | Preconditions / notes |
|------------|---------|-----------------------|
| Infrastructure / bootstrap | `docker compose up -d` then `docker compose ps` | `db`, `redis`, `backend`, and `frontend` must be healthy; `nginx` must be running. |
| Migrations | `docker compose exec -T backend uv run alembic upgrade head` | Run inside the backend container. |
| Backend tests | `uv run pytest tests/ -v` | Run from repo root. |
| Frontend prep | `cd frontend && pnpm typecheck` | Validates the React Router app graph before frontend restart / E2E. |
| Frontend unit tests | `cd frontend && pnpm test` | Runs Vitest against route modules. |
| E2E anti-flake lint | `cd frontend && pnpm test:e2e:lint` | Fails on committed `waitForTimeout(...)`. |
| E2E (deterministic gate) | `cd frontend && pnpm test:e2e --project=chromium` | Run against the full Docker stack. This is local-first and not part of the default CI workflow. |
| Smoke test | `curl -sS http://localhost:8000/api/v1/health` | Phase files may override the target. |

`./scripts/phase-gate.sh [XX]` is the preferred helper for this template.

---

## Frontend commands

```bash
cd frontend
pnpm install
pnpm typecheck
pnpm test
pnpm test:e2e:lint
pnpm test:e2e --project=chromium
pnpm build
pnpm start
```

## Manual browser investigation (Playwright CLI, opt-in)

Use this only for explicit manual debugging requests when deterministic tests do not expose a browser issue.
It is not part of default gate automation.

```bash
cd frontend

# One-off interactive browser session
pnpm playwright:cli -- open http://localhost:3000 --headed

# Inspect elements available for interaction
pnpm playwright:cli -- snapshot

# Capture evidence while reproducing a bug
pnpm playwright:cli -- screenshot
```

Prefer `pnpm test:e2e --project=chromium` for deterministic pass/fail checks, and convert manual findings into E2E specs when possible.

## Manual response compression (Caveman, opt-in)

Use this only when you explicitly want shorter agent output to reduce token usage in long debugging loops.
It is not part of `phase-gate`.

```bash
# Install once in the project
./scripts/install-caveman.sh

# Activate only when needed in a session
/caveman
# Codex trigger:
$caveman
```

Notes:
- Keep default project policy in normal response mode.
- Prefer normal mode for final docs, contracts, and handoff notes.

React Router SSR is enabled in `frontend/react-router.config.ts`. Route modules use `meta()`
exports for document title and SEO metadata.

---

## Project structure

```text
.
├── app/                    # FastAPI backend
├── alembic/                # DB migrations
├── frontend/               # React Router SSR frontend
│   ├── app/
│   │   ├── root.tsx
│   │   ├── routes.ts
│   │   └── routes/
│   └── tests/
├── tests/                  # pytest backend tests
├── docs/                   # SPEC, CONTEXT, STATE, CHANGELOG, PHASE_XX, STACK
├── docker-compose.yml
├── Dockerfile.backend
├── Dockerfile.frontend
└── AGENTS.md / CLAUDE.md
```

Before editing the frontend, read [../frontend/README.md](../frontend/README.md).
