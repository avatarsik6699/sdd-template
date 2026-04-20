# Runbook

> Template memory file for derived projects.
> Keep practical operational knowledge here so it is not lost between sessions.

## Local Development

```bash
# Fill in canonical local setup and run commands
[install command]
[dev server command]
[backend dev command]
[frontend dev command]
```

## Common Operations

| Operation | Command / Procedure | Notes |
|-----------|----------------------|-------|
| Start stack | `[command]` | `[notes]` |
| Stop stack | `[command]` | `[notes]` |
| Apply migrations | `[command]` | `[notes]` |
| Seed data | `[command]` | `[notes]` |
| Reset local state | `[command]` | `[notes]` |
| Build for production | `[command]` | `[notes]` |
| Deploy | `[command]` | `[notes]` |

## Incident Checklist

1. Identify the failing component: `[api / db / queue / frontend / external service]`
2. Check logs and recent changes: `[commands / dashboards]`
3. Validate dependencies: `[database, env vars, secrets, upstream services]`
4. Apply the documented recovery step or rollback
5. Record the outcome in `docs/KNOWN_GOTCHAS.md` or `docs/DECISIONS.md` if it reveals a lasting lesson
