# Testing

> Template memory file for derived projects.
> Document the real testing strategy so agents do not guess how quality is enforced.

## Quality Policy

- Required checks before commit: `[lint / types / unit / e2e / smoke]`
- Required checks before deploy: `[integration / migration / manual QA / monitoring]`
- Risk-based testing rule: `[how to scale test depth by change size]`

## Test Layers

| Layer | Tooling | What it proves | When it is required |
|------|---------|----------------|---------------------|
| Lint | `[tool]` | `[style / static checks]` | `[always / conditional]` |
| Types | `[tool]` | `[type safety / schema consistency]` | `[always / conditional]` |
| Unit | `[tool]` | `[function / module behavior]` | `[always / conditional]` |
| Integration | `[tool]` | `[module boundary behavior]` | `[always / conditional]` |
| E2E | `[tool]` | `[user-facing contract]` | `[always / conditional]` |
| Smoke | `[tool]` | `[deploy sanity]` | `[always / conditional]` |

## Commands

```bash
# Fill in the canonical commands for this project
[lint command]
[typecheck command]
[unit test command]
[integration test command]
[e2e test command]
[smoke test command]
```

## Testing Notes

- Fixtures / factories: `[where they live]`
- Test data / seed rules: `[how to create stable data]`
- Flaky test policy: `[what to do when a test is unreliable]`
- Coverage policy: `[if applicable]`
