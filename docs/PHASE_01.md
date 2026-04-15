# PHASE 01 — Foundation & Core Data

## Метаданные фазы
| Поле | Значение |
|------|----------|
| Фаза | `01` |
| Название | Foundation & Core Data |
| Статус | `⏳ pending` |
| Тег | `v0.1.0` |
| Зависит от | — |

---

## Цель фазы
Запустить базовую инфраструктуру: Docker, БД с миграциями, JWT-аутентификация, Nuxt-скелет, CI. Это фундамент, на котором строятся все остальные фазы.

---

## Scope (что входит)

### Backend
- [ ] Docker Compose: db (postgres), redis, backend, frontend, nginx — все healthy
- [ ] Alembic миграция `0001_users_table` применена
- [ ] `GET /api/v1/health` → `{"status": "ok", "db": "connected"}`
- [ ] `POST /api/v1/auth/login` → JWT access_token
- [ ] `GET /api/v1/auth/me` → текущий пользователь
- [ ] Seeded admin: `admin@example.com` / `changeme123`

### Frontend
- [ ] Nuxt 4 запускается без ошибок
- [ ] Страница `/login` — форма входа
- [ ] Страница `/dashboard` — заглушка после логина
- [ ] Auth guard: неаутентифицированные редиректятся на `/login`

### Тесты
- [ ] `pytest tests/ -v` — все проходят
- [ ] `cd frontend && pnpm vitest run` — все проходят
- [ ] `cd frontend && pnpm exec tsc --noEmit` — 0 ошибок

---

## Файлы фазы

### Создать / изменить
```
app/
├── main.py            # FastAPI app + CORS + X-Request-ID middleware
├── core/config.py     # Pydantic Settings
├── core/auth.py       # JWT + bcrypt + RBAC
├── db/base.py         # Base + UUID/Timestamp mixins
├── db/session.py      # async_sessionmaker
├── db/models/user.py  # User model
├── api/v1/health.py   # GET /health
├── api/v1/auth.py     # POST /login, GET /me, POST /logout
└── schemas/auth.py    # LoginRequest, TokenResponse, UserOut
alembic/versions/0001_users_table.py
frontend/app/
├── pages/login.vue
├── pages/dashboard.vue
├── layouts/default.vue
├── layouts/blank.vue
├── stores/auth.ts
├── stores/ui.ts
├── middleware/auth.global.ts
└── composables/useApi.ts
tests/
├── conftest.py
├── test_health.py
└── test_auth_api.py
```

### НЕ трогать
- Всё остальное — реализуется в последующих фазах

---

## Gate-проверки (все должны быть зелёными перед коммитом)

```bash
# 1. Инфраструктура
docker compose up -d db redis
docker compose ps  # db + redis: healthy

# 2. Миграции
DATABASE_URL=postgresql+asyncpg://app_user:changeme@localhost:5432/myapp \
  uv run alembic upgrade head

# 3. Backend тесты
uv run pytest tests/ -v

# 4. Health check
curl -s http://localhost:8000/api/v1/health
# → {"status":"ok","db":"connected"}

# 5. Frontend
cd frontend
pnpm install --frozen-lockfile
pnpm exec tsc --noEmit
pnpm vitest run
```

---

## Атомарный коммит
```
feat(phase-01): foundation — docker, db, jwt auth, nuxt skeleton
```
