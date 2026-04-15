# ТЕХНИЧЕСКОЕ ЗАДАНИЕ (SPEC.md): `[PROJECT_NAME]`

## Метаданные
| Поле | Значение |
|------|----------|
| Версия документа | `v1.0` |
| Дата | `[DATE]` |
| Архитектор / Владелец | `[OWNER]` |
| Стек | Nuxt 4 (Vue 3.5+, TS, pnpm), FastAPI latest, SQLAlchemy 2.0 (async), PostgreSQL 18, Redis 8, Docker Compose |
| AI-агент | Claude Code (Agent Mode) |
| Домен | `[DOMAIN — краткое описание предметной области]` |

---

## 1. Обзор проекта и цели

### 1.1. Проблема
<!-- Какую проблему решает этот проект? Что происходит без него? -->

### 1.2. Цель и метрики успеха
<!-- Чего нужно достичь? Какие метрики подтвердят успех? -->
- ...

### 1.3. Границы проекта
| Включено | Исключено |
|----------|-----------|
| ... | ... |

---

## 2. Доменный контекст

### 2.1. Роли и права
| Роль | Возможности | Ограничения |
|------|-------------|-------------|
| `Admin` | ... | ... |
| `Architect` | ... | ... |
| `Expert` | ... | ... |

### 2.2. Ключевые сущности
<!-- Перечислите основные сущности и их связи -->
`Entity1 → Entity2 → Entity3`

---

## 3. Модель данных (SQLAlchemy 2.0 Async)

```text
<!-- Опишите таблицы БД -->
table_name(id UUID PK, field1 TYPE, field2 TYPE, created_at TIMESTAMPTZ)
```

---

## 4. API и бэкенд (FastAPI + Python)

### 4.1. Архитектура
```
app/
├── api/v1/   (routers: ...)
├── core/     (config, auth, exceptions)
├── db/       (async_session, models, alembic)
├── services/ (domain services)
└── schemas/  (Pydantic v2 request/response)
```

### 4.2. Основные эндпоинты
| Метод | Путь | Описание |
|-------|------|----------|
| `GET` | `/api/v1/health` | Health check |
| `POST` | `/api/v1/auth/login` | JWT login |
| `GET` | `/api/v1/auth/me` | Current user |
| ... | ... | ... |

### 4.3. Требования к коду
- Type hints 100%, Pydantic v2, async/await
- Зависимости через `uv` (`pyproject.toml` + `uv.lock`); `pip-tools` не использовать
- RBAC через FastAPI Dependencies + JWT scopes
- No hardcoded secrets — только `.env` / Pydantic Settings

---

## 5. Фронтенд (Nuxt 4 + Vue 3.5+ + TypeScript)

### 5.1. Страницы
```
pages/
├── dashboard.vue
├── [feature]/index.vue
└── [feature]/[id].vue
```

### 5.2. Компоненты и сторы
```
components/
├── ui/    (buttons, modals, toasts)
└── [feature]/
stores/    (Pinia: auth, ui, ...)
composables/ (useApi, ...)
```

---

## 6. Инфраструктура и CI/CD

### 6.1. Docker
```
docker-compose.yml  (backend, frontend, postgres, redis, nginx)
Dockerfile.backend
Dockerfile.frontend
```

### 6.2. CI (GitHub Actions)
- lint (ruff, tsc --noEmit)
- test-backend (pytest + postgres service)
- test-frontend (vitest)
- build (docker images)

---

## 7. Тестирование
| Уровень | Фреймворк | Покрытие |
|---------|-----------|----------|
| Backend Unit/Integration | pytest + asyncio | ≥70% |
| Frontend Unit | Vitest | ≥70% |

---

## 8. Этапы разработки (AI-Optimized Phases)

> Правило для AI-агента: реализуй фазы строго по порядку. После каждой фазы запускай gate-проверки, коммить атомарно, обновляй `STATE.md`.

### Фаза 1: Foundation & Core Data
- **Scope**: Docker infra, DB models, Alembic, Auth/JWT, Nuxt skeleton
- **Gate**: `docker compose up` → healthy, `pytest` → pass, `tsc --noEmit` → OK, `vitest` → pass

### Фаза 2: [FEATURE]
- **Scope**: ...
- **Gate**: ...

<!-- Добавьте фазы по мере необходимости -->

---

## 9. Глоссарий
| Термин | Определение |
|--------|-------------|
| `Gate` | Набор проверок (тесты, линт, type-check), блокирующий переход к следующей фазе |
| ... | ... |

---

> **Инструкция для AI-агента:**
> Прочитайте SPEC.md полностью. Подтвердите понимание ограничений и модели фазовой разработки. Начните с Фазы 1. НЕ генерируйте Фазу 2+ пока не пройдены gate-проверки Фазы 1. Сначала план → ожидание подтверждения → код → тесты → коммит.
