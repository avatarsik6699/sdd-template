# TECHNICAL SPECIFICATION (SPEC.md): `[PROJECT_NAME]`

> **For AI agent**: Read this file in full before starting any phase.
> Confirm understanding of constraints and the phased development model.
> When this file changes, run `/spec-sync [description of change]` immediately.

## Metadata

| Field | Value |
|-------|-------|
| Document Version | `v1.0` |
| Date | `[DATE]` |
| Architect / Owner | `[OWNER]` |
| Contract Version | `v1.0` (see `docs/CONTEXT.md`) |
| Stack | React 19 + React Router 7 SSR (TS, pnpm), FastAPI latest, SQLAlchemy 2.0 (async), PostgreSQL 18, Redis 8, Docker Compose |
| AI Agent | Claude Code (Agent Mode) |
| Domain | `[DOMAIN — brief description of the subject area]` |

---

## 1. Project Overview and Goals

### 1.1 Problem
<!-- What problem does this project solve? What happens without it? -->

### 1.2 Goal and Success Metrics
<!-- What must be achieved? Which metrics confirm success? -->
- ...

### 1.3 Project Boundaries
| Included | Excluded |
|----------|----------|
| ... | ... |

---

## 2. Domain Context

### 2.1 Roles and Permissions
| Role | Capabilities | Restrictions |
|------|-------------|--------------|
| `Admin` | ... | ... |
| `Architect` | ... | ... |
| `Expert` | ... | ... |
| `AI_Agent` | Implements phases, runs gate checks | No push to main/develop |

### 2.2 Key Entities
<!-- List core entities and their relationships -->
`Entity1 → Entity2 → Entity3`

---

## 3. Data Model (SQLAlchemy 2.0 Async)

```text
<!-- Describe DB tables -->
table_name(id UUID PK, field1 TYPE NOT NULL, field2 TYPE, created_at TIMESTAMPTZ)
```

---

## 4. API and Backend (FastAPI + Python)

### 4.1 Architecture
```
app/
├── api/v1/     (routers: ...)
├── core/       (config, auth, exceptions)
├── db/         (async_session, models, alembic)
├── services/   (domain services)
└── schemas/    (Pydantic v2 request/response)
```

### 4.2 Core Endpoints
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET`  | `/api/v1/health` | — | Health check |
| `POST` | `/api/v1/auth/login` | — | JWT login |
| `GET`  | `/api/v1/auth/me` | JWT | Current user |
| ... | ... | ... | ... |

### 4.3 Code Requirements
- 100% type hints, Pydantic v2, async/await throughout
- Dependencies via `uv` (`pyproject.toml` + `uv.lock`); do not use `pip-tools`
- RBAC via FastAPI `Depends` + JWT scopes
- No hardcoded secrets — use `.env` / Pydantic Settings only

---

## 5. Frontend (React Router SSR + React 19 + TypeScript)

### 5.1 Pages
```
pages/
├── dashboard.vue
├── [feature]/index.vue
└── [feature]/[id].vue
```

### 5.2 Components and Stores
```
components/
├── ui/        (buttons, modals, toasts)
└── [feature]/
stores/        (Pinia: auth, ui, ...)
composables/   (useApi, ...)
```

### 5.3 Design References

<!-- Screenshots attached during /spec-init. One entry per key screen.
     Format: `Screen name — brief description (route, key components, notable interactions)`
     Leave the comment below if no design assets were provided. -->

<!-- none provided -->

---

## 6. Infrastructure and CI/CD

### 6.1 Docker
```
docker-compose.yml  (backend, frontend, postgres, redis, nginx)
Dockerfile.backend
Dockerfile.frontend
```

### 6.2 CI (GitHub Actions)
- `lint` — ruff, tsc --noEmit
- `test-backend` — pytest + postgres service
- `test-frontend` — vitest
- `build` — docker images

---

## 7. Non-Functional Requirements

| Category | Requirement |
|----------|-------------|
| Security | No hardcoded secrets; bcrypt ≥12 rounds; JWT expiry ≤60 min |
| Test coverage | Backend ≥70%, Frontend ≥70% |
| Type safety | 100% type hints (Python), strict TypeScript |
| Performance | Health endpoint p99 < 200ms |
| Environments | `development`, `staging`, `production` |

---

## 8. Development Phases (AI-Optimized)

> **AI agent rule**: implement phases strictly in order.
> After each phase: run gate checks, commit atomically, update `STATE.md`.
> Do NOT start Phase N+1 until Phase N gate is green.
> ⚠️ When this file changes, run `/spec-sync [description]` immediately.

### Phase 1: Foundation & Core Data
- **Scope**: Docker infra, DB models, Alembic, Auth/JWT, React Router SSR skeleton, CI
- **Gate**: `docker compose up` → healthy, `pytest` → pass, `tsc --noEmit` → OK, `vitest` → pass

### Phase 2: [FEATURE]
- **Scope**: ...
- **Gate**: ...

<!-- Add phases as needed. Use /phase-init N to scaffold PHASE_XX.md -->

---

## 9. Glossary

| Term | Definition |
|------|------------|
| `Gate` | Set of checks (tests, lint, type-check) that must pass before moving to the next phase |
| `CONTEXT.md` | Living technical contract: current DB schema, active endpoints, TS types, env vars |
| `STATE.md` | Operational tracker: phase statuses, blockers, expert feedback |
| `CHANGELOG.md` | History of spec/architecture changes and their impact |
| ... | ... |
