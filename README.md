# [PROJECT_NAME]

> SDD template — FastAPI + Nuxt 4 + PostgreSQL + Docker + GitHub Actions

---

## Getting Started

Run the init script once after cloning. It replaces all placeholders and creates `.env`:

```bash
./scripts/init-project.sh <project-slug> <domain> [admin-email]

# Example:
./scripts/init-project.sh user-dashboard example.com admin@example.com
```

The script:
- Derives a display name from the slug (`user-dashboard` → `User Dashboard`)
- Generates a random `SECRET_KEY` and `POSTGRES_PASSWORD`
- Creates `.env` from `.env.example` with all values filled in
- Replaces placeholders in source files, `nginx.conf`, CI workflow, and docs
- Copies `CLAUDE.md` to the project root

After the script, configure [GitHub Secrets](#deployment) and run `docker compose up --build`.

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
pnpm --version          # 10+
```

### 2. Environment

```bash
cp .env.example .env
# Generate a secure SECRET_KEY:
echo "import secrets; print(secrets.token_hex(32))" | uv run -
# Paste the result into SECRET_KEY= in .env
```

### 3. Start dev stack

```bash
docker compose up --build
# Backend:  http://localhost:8000
# Frontend: http://localhost:3000
```

Migrations run automatically on backend startup. Hot-reload is active for both services — changes to `app/` and `frontend/` are reflected immediately without restarting containers.

---

## First-time local setup (for IDE and git hooks)

These steps are needed once after cloning. They do not affect Docker — they set up your local editor and git workflow.

### Install Python dependencies (for IntelliSense and mypy)

```bash
uv sync --dev
# VS Code: Ctrl+Shift+P → "Python: Select Interpreter" → select .venv/bin/python
```

### Install frontend dependencies (for TypeScript and Vue IntelliSense)

```bash
cd frontend && pnpm install
```

### Activate pre-commit hooks

```bash
uv run pre-commit install
```

After this, ruff linting and formatting run automatically before every `git commit`.

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
├── .claude/
│   └── skills/
│       ├── spec-sync/       # /spec-sync  — propagate SPEC.md changes
│       ├── phase-gate/      # /phase-gate — run all gate checks
│       ├── context-update/  # /context-update — update CONTEXT.md after phase
│       └── phase-init/      # /phase-init — scaffold next PHASE_XX.md
├── app/                     # FastAPI backend
│   ├── api/v1/              # Routers (health, auth + your routers)
│   ├── core/                # config.py, auth.py
│   ├── db/                  # base.py, session.py, models/
│   └── schemas/             # Pydantic schemas
├── alembic/                 # DB migrations
├── frontend/                # Nuxt 4 app
│   └── app/
│       ├── layouts/         # default.vue, blank.vue
│       ├── middleware/       # auth.global.ts
│       ├── composables/     # useApi.ts
│       ├── stores/          # auth.ts, ui.ts
│       └── pages/           # login.vue, dashboard.vue
├── tests/                   # pytest integration tests
├── docs/
│   ├── SPEC.md              # Strategic brief: goals, roles, domain rules
│   ├── CONTEXT.md           # Living contract: DB schema, endpoints, types (v1.0)
│   ├── STATE.md             # Operational tracker: phase statuses, blockers
│   ├── CHANGELOG.md         # History of spec/architecture changes
│   ├── PHASE_TEMPLATE.md    # Template for new phases
│   └── PHASE_01.md          # Phase 1 mini-spec
├── docker-compose.yml
├── Dockerfile.backend
├── Dockerfile.frontend
├── nginx.conf
├── pyproject.toml
├── .env.example
└── CLAUDE.md                # AI agent rules + skills reference + phase lifecycle
```

---

## SDD Workflow

This template follows a **Spec-Driven Development** cycle where you act as architect and the AI acts as a precision implementer.

### Phase lifecycle (10 steps)

```
1.  Fill in docs/SPEC.md                → strategic brief, domain rules
2.  /phase-init N                       → scaffolds docs/PHASE_N.md
3.  Fill in Contracts + Files sections  → architect defines the interface
4.  AI implements (feat/phase-N branch) → scoped to phase only
5.  /phase-gate N                       → pytest + tsc + vitest + docker
6.  git commit                          → feat(phase-N): description
7.  /context-update N                   → syncs CONTEXT.md, STATE.md, CHANGELOG.md
8.  PR to develop → review → merge
9.  git tag -a v0.N.0 -m "Phase N: ..."
10. /phase-init N+1                     → repeat
```

### Skills (slash commands)

| Command | When to use |
|---------|-------------|
| `/spec-sync [description]` | Immediately after editing `docs/SPEC.md` |
| `/phase-gate [N]` | Before committing — runs all checks, reports PASS/FAIL |
| `/context-update [N]` | After gate passes — bumps CONTEXT.md version, updates STATE.md |
| `/phase-init [N]` | To scaffold the next `PHASE_XX.md` from the template |
| `/my-review [file]` | Code review of specific files |

### Key documents

| File | What it answers |
|------|----------------|
| `docs/SPEC.md` | What are we building? What are the rules? |
| `docs/CONTEXT.md` | What is in the system right now? (version-controlled contract) |
| `docs/STATE.md` | Where are we in the process? What is blocked? |
| `docs/CHANGELOG.md` | Why did the contract change? Which phases were affected? |
| `docs/PHASE_XX.md` | What exactly should the AI implement this iteration? |

### When SPEC.md changes

```bash
# 1. Edit docs/SPEC.md
# 2. Immediately run:
/spec-sync "description of what changed and why"
# 3. Review generated changes in CHANGELOG.md, STATE.md, affected PHASE_XX.md files
# 4. Resolve any ⚠️ NEEDS_REVIEW phases before implementing
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
