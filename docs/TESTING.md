# Testing

This template ships with a concrete reference implementation, so these checks are real and should
stay aligned with `/phase-gate`, CI, and the phase docs.

## Quality Policy

- Required checks before commit: `pytest`, frontend type-check, `vitest`, smoke check, and Playwright when the full stack is already up
- Required checks before deploy: migrations applied, CI green, Docker images build successfully, and a manual browser sanity pass on the target environment
- Risk-based testing rule: docs-only changes may skip code tests; backend or frontend behavior changes should run the affected local checks; contract, auth, migration, or infra changes should run the full gate

## Test Layers

| Layer | Tooling | What it proves | When it is required |
|------|---------|----------------|---------------------|
| Lint | `uv run ruff check .` and `cd frontend && pnpm lint` | Python and frontend static hygiene | Required before PR / CI |
| Types | `cd frontend && pnpm nuxt prepare && pnpm typecheck` | Nuxt, Vue, and generated types stay aligned | Required before commit when frontend code changes |
| Backend tests | `uv run pytest tests/ -v` | API/auth behavior and DB interactions | Required before commit when backend code changes |
| Frontend unit | `cd frontend && pnpm nuxt prepare && pnpm test` | Store and component behavior | Required before commit when frontend code changes |
| E2E | `cd frontend && pnpm test:e2e` | Full user-facing flow against the running stack | Required by the gate when `db`, `redis`, `backend`, `frontend`, and `nginx` are already healthy |
| Smoke | `curl -s http://localhost:8000/api/v1/health` | Backend is reachable and DB-backed health responds | Required before commit for application phases |

## Commands

```bash
uv run ruff check .
cd frontend && pnpm lint
cd frontend && pnpm nuxt prepare && pnpm typecheck
uv run pytest tests/ -v
cd frontend && pnpm nuxt prepare && pnpm test
cd frontend && pnpm test:e2e
curl -s http://localhost:8000/api/v1/health
```

## Testing Notes

- Fixtures / factories: backend test setup lives in `tests/conftest.py`; it uses in-memory SQLite locally and Postgres in CI when `DATABASE_URL` is set
- Test data / seed rules: auth defaults come from the migration seed; tests should prefer isolated fixture-created state over shared mutable seed data
- Flaky test policy: treat `.nuxt`-missing failures as setup failures first; re-run after `pnpm nuxt prepare` before debugging test logic
- Coverage policy: CI currently enforces green checks rather than percentage thresholds; if a derived project adopts thresholds, update this file and the phase gate together
