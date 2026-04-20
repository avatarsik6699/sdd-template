# PHASE [XX] — [Phase Title]

<!-- TOKEN BUDGET: keep this file under 10,000 tokens. Be concise. -->

## Phase Metadata

| Field | Value |
|-------|-------|
| Phase | `[XX]` |
| Title | [Phase Title] |
| Status | `⏳ pending` |
| Tag | `v0.[XX].0` |
| Depends on | PHASE_[XX-1] gate passing |
| CONTEXT.md version | `[VERSION — snapshot at time of writing, e.g. v1.1]` |

---

## Phase Goal

<!-- 2–4 sentences: what does this phase deliver and why does it matter?
     Link to a SPEC.md section if relevant. -->

---

## Scope

### Backend
- [ ] [task]

### Frontend
- [ ] [task]

### Tests
- [ ] `uv run pytest tests/ -v` — all pass
- [ ] `cd frontend && pnpm vitest run` — all pass
- [ ] `cd frontend && pnpm exec tsc --noEmit` — 0 errors
- [ ] `cd frontend && pnpm test:e2e` — all pass (requires full Docker stack up)
- [ ] At least one Playwright spec covers each user-facing flow introduced in this phase

---

## Files

### Create / modify
~~~
[list files relative to repo root]
~~~

### Do NOT touch
- [List files / directories out of scope for this phase]

---

## Contracts

> This section is the source of truth for `/context-update`. Fill it in **before** handing to AI.

### New DB tables / columns
~~~
table_name(col TYPE NOT NULL, ...)
~~~
None

### New API endpoints
| Method | Path | Auth | Response |
|--------|------|------|----------|
| `GET` | `/api/v1/[path]` | JWT | `{"field": type}` |

None

### New TypeScript types / Pinia stores
```typescript
// [TypeName] — describe what it represents
```
None

### New env vars (add to `.env.example`)
| Key | Example value | Required |
|-----|---------------|----------|
| `VAR_NAME` | `value` | yes |

None

---

## Gate Checks

Run `/phase-gate [XX]` before committing.

`/phase-gate` returns full PASS only when:
- Automated checks are green
- All architect review items below are resolved (checked off)

```bash
# 1. Infrastructure
docker compose up -d db redis
docker compose ps  # db + redis must show: healthy

# 2. Migrations
DATABASE_URL=postgresql+asyncpg://app_user:changeme@localhost:5432/myapp \
  uv run alembic upgrade head

# 3. Backend tests
uv run pytest tests/ -v

# 4. Smoke test
curl -s http://localhost:8000/api/v1/[your-endpoint]
# expected: [describe expected response]

# 5. Frontend unit + type check
cd frontend
pnpm exec tsc --noEmit
pnpm vitest run

# 6. E2E (Playwright) — requires full stack healthy:
#    db, redis, backend, frontend, nginx
docker compose up -d            # if not already running
docker compose ps               # verify all five services are healthy
pnpm test:e2e                   # parses test-results/junit.xml
# Report lives at frontend/playwright-report/index.html
```

---

## Architect Review Notes

Use this section after manual verification. Add one checkbox item per issue the architect wants fixed before the phase can close.
Leave the item unchecked while it is still open. Check it off only after the fix is implemented and re-verified.
If manual verification found nothing, keep the default checked line below.

- [x] No architect review issues recorded

---

## Atomic Commit Message

```
feat(phase-[XX]): [short description — what was built, not how]
```

---

## Post-Phase Checklist

- [ ] All automated gate checks green
- [ ] All architect review notes resolved
- [ ] `docs/CONTEXT.md` updated — run `/context-update [XX]`
- [ ] `docs/STATE.md` phase row updated to `✅ done`
- [ ] `docs/CHANGELOG.md` entry added (if CONTEXT.md version bumped)
- [ ] Committed atomically on `feat/phase-[XX]` branch
- [ ] Tag created after merge to develop: `git tag -a v0.[XX].0 -m "Phase [XX]: [title]"`
