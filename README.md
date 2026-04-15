# [PROJECT_NAME]

> SDD template — FastAPI + Nuxt 4 + PostgreSQL + Docker + GitHub Actions

Replace `[PROJECT_NAME]` everywhere with your actual project name before starting development.

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

## Quick Start

### 1. Prerequisites

```bash
docker --version        # Docker 24+
docker compose version  # v2+
uv --version            # any recent
node --version          # 22+
pnpm --version          # 9+
```

### 2. Environment

```bash
cp .env.example .env
# Generate a secure SECRET_KEY:
python -c "import secrets; print(secrets.token_hex(32))"
# Paste the result into SECRET_KEY= in .env
```

### 3. Start infrastructure

```bash
docker compose up -d db redis
docker compose ps   # both should show: healthy
```

### 4. Run migrations

```bash
DATABASE_URL=postgresql+asyncpg://app_user:changeme@localhost:5432/myapp \
  uv run alembic upgrade head
```

### 5. Run backend

```bash
uv sync --dev
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 6. Run frontend

```bash
cd frontend
pnpm install
pnpm dev
```

### 7. Full Docker stack

```bash
docker compose up -d --build
# Backend: http://localhost:8000
# Frontend: http://localhost:3000
# Via nginx: http://localhost
```

---

## Gate Checklist (Phase 01)

| Gate | Command | Expected |
|------|---------|----------|
| Docker infra | `docker compose up -d db redis && docker compose ps` | db + redis: healthy |
| Migrations | `uv run alembic upgrade head` | `0001` applied |
| Health API | `curl localhost:8000/api/v1/health` | `{"status":"ok","db":"connected"}` |
| pytest | `uv run pytest tests/ -v` | all passed |
| tsc | `cd frontend && pnpm exec tsc --noEmit` | 0 errors |
| vitest | `cd frontend && pnpm vitest run` | all passed |

---

## Default credentials

```
Email:    admin@example.com
Password: changeme123
```

Change these in `alembic/versions/0001_users_table.py` before going to production.

---

## Project structure

```
.
├── app/                    # FastAPI backend
│   ├── api/v1/             # Routers (health, auth + your routers)
│   ├── core/               # config.py, auth.py
│   ├── db/                 # base.py, session.py, models/
│   └── schemas/            # Pydantic schemas
├── alembic/                # DB migrations
├── frontend/               # Nuxt 4 app
│   └── app/
│       ├── layouts/        # default.vue, blank.vue
│       ├── middleware/     # auth.global.ts
│       ├── composables/    # useApi.ts
│       ├── stores/         # auth.ts, ui.ts
│       └── pages/          # login.vue, dashboard.vue
├── tests/                  # pytest integration tests
├── docs/
│   ├── SPEC.md             # Master specification
│   ├── PHASE_01.md         # Phase instructions
│   ├── CONTEXT.md          # Current DB/API/types snapshot (update after each phase)
│   └── STATE.md            # Phase progress tracker
├── docker-compose.yml
├── Dockerfile.backend
├── Dockerfile.frontend
├── nginx.conf
├── pyproject.toml
├── .env.example
└── CLAUDE.md               # AI agent rules
```

---

## SDD Workflow

```
1. Fill in docs/SPEC.md  (what to build)
2. Write docs/PHASE_01.md (what to build in this iteration)
3. AI agent implements the phase
4. Run gate checks → all green
5. Commit atomically: feat(phase-01): ...
6. Update docs/CONTEXT.md and docs/STATE.md
7. Write docs/PHASE_02.md → repeat
```

---

## Adding a new migration

```bash
uv run alembic revision --autogenerate -m "add_your_table"
uv run alembic upgrade head
```

## Stop everything

```bash
docker compose down       # stop containers, keep data
docker compose down -v    # stop containers + delete postgres data
```
