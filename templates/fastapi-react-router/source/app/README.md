# Backend

FastAPI + SQLAlchemy 2.0 async + Alembic + Pydantic v2. Python 3.13+.

This file is the backend style guide. Read it before editing anything under [app/](.) or [tests/](../tests/). Root-level project rules live in [../AGENTS.md](../AGENTS.md); this file only covers what's module-specific.

---

## Architecture

The backend follows a **modular DDD layout**: each bounded context (domain) is a self-contained module. Cross-cutting infrastructure lives outside the modules.

```
app/
├── main.py              composition root: FastAPI app, lifespan, middleware, router
├── core/                framework infrastructure
│   ├── config.py        global Settings (Pydantic Settings)
│   ├── constants.py     API_V1_PREFIX, REQUEST_ID_HEADER
│   ├── exceptions.py    AppException base — domain exceptions inherit from here
│   ├── logging.py       configure_logging()
│   └── middleware.py    register_middleware(app) — request-id middleware
├── db/                  shared persistence infrastructure
│   ├── base.py          declarative Base + UUIDMixin + TimestampMixin
│   └── session.py       async engine, AsyncSessionLocal, get_db, init_db, close_db
├── shared/              domain-agnostic reusables (envelopes, types, generic deps)
├── api/v1/router.py     APIRouter(prefix="/api/v1") — aggregates every module's router
└── modules/             bounded contexts
    ├── users/           User table, profile, roles
    ├── auth/            login, JWT, password hashing, current-user dep, role guards
    └── health/          /health endpoint
```

### Module internal layout

Each module under [modules/](modules/) follows the same shape:

| File | Contains |
|------|----------|
| `__init__.py` | Public API — re-exports services, schemas, exceptions. Cross-module imports MUST come through this file. |
| `api.py` | FastAPI `APIRouter`. Thin handlers — delegate to the service. |
| `service.py` | Use cases / domain logic. Raises domain exceptions; returns ORM entities or DTOs. |
| `repository.py` | SQLAlchemy queries. Constructor takes `AsyncSession`. |
| `models.py` | ORM models owned by this module. |
| `schemas.py` | Pydantic request/response DTOs. |
| `dependencies.py` | FastAPI `Depends` factories — wires repo → service. |
| `exceptions.py` | Domain exceptions inheriting from `app.core.exceptions.AppException`. |
| `constants.py` | Module-local constants (claim names, length limits, etc.). |
| `config.py` | Module-local config view; reads from global `Settings`. |
| `utils.py` | Pure helpers (no I/O, no FastAPI). |

Empty placeholder files are intentional — they fix the layout so any new contributor knows where things go.

### Layering and import rules

| Direction | Allowed? |
|-----------|----------|
| `modules.* → shared, core, db` | ✅ |
| `shared → core` | ✅ |
| `db → core` | ✅ |
| `core, shared → modules` | ❌ |
| `modules.X → app.modules.Y` (package root) | ✅ |
| `modules.X → app.modules.Y.repository / .models / .utils` | ❌ |

- **Public API of a module = its `__init__.py`.** Anything not re-exported there is private. Cross-module access goes only through the package root: `from app.modules.users import UserService`.
- **No circular module dependencies.** If two modules need each other, factor the shared piece into [shared/](shared/) or merge them.
- **Module owns its tables.** Cross-module DB joins are forbidden — call the other module's service via `Depends`.
- **Never return ORM models from handlers.** Validate into a Pydantic schema first (e.g. `UserOut.model_validate(user)`).

### Module communication

Modules talk via injected services through FastAPI `Depends`:

```python
# modules/auth/dependencies.py
def get_auth_service(
    user_service: UserService = Depends(get_user_service),
) -> AuthService:
    return AuthService(user_service=user_service)
```

`auth → users` is the only cross-module dependency today. The reverse direction is forbidden.

For domain events / pub-sub: not used yet. If a future module needs to react to events from another (e.g. `notifications` reacts to `user.created`), introduce a small in-process event bus in `shared/` rather than reaching across module boundaries.

---

## Style & lint

Config lives in [../pyproject.toml](../pyproject.toml).

- **Ruff** — `select = ["E", "F", "I", "UP"]`, line-length 100, `target-version = "py313"`. Run via the pre-commit hook.
- **Mypy** — `disallow_untyped_defs = True`, `warn_return_any = True`, `ignore_missing_imports = True`. Every function signature gets annotations.
- **Pytest** — `asyncio_mode = "auto"` — don't decorate async tests with `@pytest.mark.asyncio`; it's implicit.

Format & lint before committing:

```bash
uv run ruff format app tests
uv run ruff check --fix app tests
uv run mypy app
```

---

## Naming

- Modules and functions: `snake_case`.
- Classes and enums: `PascalCase`.
- Enums backing DB columns: subclass `StrEnum`, lowercase member values matching the Postgres type (`class UserRole(StrEnum): admin = "admin"`).
- Absolute imports rooted at `app.*` — never relative.
- Files inside a module use singular nouns where applicable (`models.py` holds related entities; promote to `models/` package when a module gains many).

---

## Key patterns

- **Async session dependency**: handlers/services that need DB take `session: AsyncSession = Depends(get_db)` from [db/session.py](db/session.py). Never instantiate a session inline.
- **Repositories take a session, services take a repository.** Wire them in `dependencies.py`:
  ```python
  def get_user_repository(session: AsyncSession = Depends(get_db)) -> UserRepository:
      return UserRepository(session)

  def get_user_service(repo: UserRepository = Depends(get_user_repository)) -> UserService:
      return UserService(repo)
  ```
- **Domain exceptions = HTTP-aware.** Subclass [`AppException`](core/exceptions.py); FastAPI renders status/headers automatically:
  ```python
  class UserNotFound(AppException):
      status_code = 404
      detail = "User not found"
  ```
- **Authentication**: `Depends(get_current_user)` from [modules/auth](modules/auth) returns the authenticated `User`. For role guards: `Depends(require_role(UserRole.admin))`.
- **Config via env**: read settings from `get_settings()` in [core/config.py](core/config.py). Pydantic Settings reads `.env` automatically — never call `os.getenv` directly in handlers.
- **Migrations with seed data**: Alembic autogenerate covers schema. Use `op.execute()` for seed rows and for typed Postgres enum DDL (`CREATE TYPE ... AS ENUM (...)`). See [../alembic/versions/0001_users_table.py](../alembic/versions/0001_users_table.py).
- **Request IDs**: middleware in [core/middleware.py](core/middleware.py) (registered from [main.py](main.py)) adds an `X-Request-ID` header to every response. Don't reinvent this per-router.
- **Schemas, not models, on the wire**: handlers return Pydantic schemas from `modules/<name>/schemas.py`. Never return an ORM model directly — it leaks columns like `hashed_password` and locks the API to the DB shape.

---

## Tests

Pytest fixtures are in [../tests/conftest.py](../tests/conftest.py):

- `test_engine` — session-scoped async engine. SQLite in-memory by default; if `DATABASE_URL` is set in the env, uses that DB instead (for CI against Postgres).
- `db_session` — per-test `AsyncSession` with automatic rollback.
- `client` — `httpx.AsyncClient` wired to the FastAPI app via `ASGITransport`. Use for integration tests.

Run:

```bash
uv run pytest tests/ -v                    # default: SQLite
DATABASE_URL=... uv run pytest tests/ -v   # against Postgres
```

Naming: `tests/test_<resource>.py`. Fixture-style factories over module-level test data.

Tests may import a module's public surface (`from app.modules.users import User, UserRole`) and its public utilities (`from app.modules.auth import hash_password, create_access_token`). Tests should not reach into `<module>.repository` or `<module>.service` internals — go through the public API.

---

## Mandatory rules (duplicated locally — these are load-bearing)

These two rules are repeated here because an AI editing inside [app/](.) often won't read the root [AGENTS.md](../AGENTS.md) first, and missing either one costs a lot of tokens.

1. **Use up-to-date docs before writing code against any external library** — FastAPI, SQLAlchemy, Pydantic, Alembic, httpx, python-jose, bcrypt, or any third-party package. Prefer Context7 via MCP when available, then `ctx7` CLI, then official docs. Do NOT rely on training data. Full rule in [../AGENTS.md](../AGENTS.md#library-documentation-lookup).

2. **On `EACCES` / `EPERM` / "Permission denied"** — stop immediately, post the handoff message from [../docs/KNOWN_GOTCHAS.md](../docs/KNOWN_GOTCHAS.md#docker-owned-files-break-host-operations-eacces--eperm--read-only) to the user with the real path, wait for the keyword `continue` before retrying. Never `sudo`, `chmod`, or loop. Short summary in [../AGENTS.md](../AGENTS.md#filesystem-permission-failures).

---

## Pointers

- Project-wide rules & phase lifecycle — [../AGENTS.md](../AGENTS.md)
- Strategic brief — [../docs/SPEC.md](../docs/SPEC.md)
- Current contract version — [../docs/CONTEXT.md](../docs/CONTEXT.md)
- Architecture decision record — [../docs/DECISIONS.md](../docs/DECISIONS.md)
- Frontend style guide — [../frontend/README.md](../frontend/README.md)
