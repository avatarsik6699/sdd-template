# Frontend

Nuxt 4 SPA with **Feature-Sliced Design (FSD)** architecture, Tailwind CSS, Nuxt UI, Pinia, and i18n.

---

## Architecture: Feature-Sliced Design

The `app/` directory follows [FSD](https://feature-sliced.design/) layering. Layers are listed from most abstract to most business-specific. **Higher layers may import from lower layers, never the reverse.**

```
app/
├── pages/          # Nuxt routing — thin page shells, compose from widgets/features
├── layouts/        # Nuxt layouts — compose from widgets
├── middleware/      # Nuxt route guards
├── plugins/         # Nuxt plugins (HTTP client init)
├── assets/          # Global styles
│
├── widgets/         # Compound UI blocks (combine features + entities)
│   └── sidebar/ui/sidebar-nav.vue
│
├── features/        # User-facing feature slices
│   └── auth/
│       └── model/auth-store.ts   # Pinia auth store
│
└── shared/          # Reusable code — zero business logic
    ├── api/         # Typed API composables
    │   └── use-api-fetch.ts
    ├── lib/         # Utilities and helpers
    │   └── safe-cookie.ts
    ├── model/       # Shared Pinia stores
    │   └── ui-store.ts
    └── types/       # Auto-generated and shared types
        └── schema.ts
```

### Layer responsibilities

| Layer | Contains | May import from |
|-------|----------|-----------------|
| `pages/` | Route entry points | `widgets`, `features`, `shared` |
| `layouts/` | App shell templates | `widgets`, `shared` |
| `widgets/` | Composite UI blocks | `features`, `entities`, `shared` |
| `features/` | Business interactions | `entities`, `shared` |
| `entities/` | Business entities | `shared` |
| `shared/` | Infrastructure, utilities | nothing project-internal |

### Naming convention

All files use **kebab-case**: `auth-store.ts`, `use-api-fetch.ts`, `safe-cookie.ts`, `sidebar-nav.vue`.  
Functions and exports remain camelCase per JavaScript convention.

### Adding new code

- **New page** → `app/pages/my-page.vue` (Nuxt auto-routing)
- **New feature** → `app/features/my-feature/model/my-feature-store.ts` + `ui/` subfolder if it has components
- **New widget** → `app/widgets/my-widget/ui/my-widget.vue` (auto-imported by Nuxt)
- **Shared utility** → `app/shared/lib/my-util.ts`
- **Shared composable** → `app/shared/api/use-my-composable.ts`

### Path aliases

Configured in `nuxt.config.ts` for clean cross-layer imports:

| Alias | Resolves to |
|-------|-------------|
| `@shared` | `app/shared/` |
| `@features` | `app/features/` |
| `@widgets` | `app/widgets/` |

Example: `import { useAuthStore } from '@features/auth/model/auth-store'`

---

## Development

```bash
# Install dependencies
pnpm install

# Start dev server (http://localhost:3000)
pnpm dev

# Type check
pnpm typecheck

# Lint
pnpm lint
pnpm lint:fix

# Build for production
pnpm build
```

---

## Testing

### Unit tests (Vitest)

```bash
pnpm test
```

Tests live in `tests/` alongside `tests/e2e/`. Unit tests import directly from `app/` using relative paths.

### E2E tests (Playwright)

Requires a running application (dev or Docker):

```bash
# Docker stack
docker-compose up -d

# Install browsers (first time only)
pnpm test:e2e:install

# Run headlessly
pnpm test:e2e

# Run with UI runner (debugging)
pnpm test:e2e:ui
```

Default base URL: `http://localhost:3000`. Override with `PLAYWRIGHT_BASE_URL`.

### Writing testable components

- Use `data-testid` attributes for elements that tests interact with
- Prefer kebab-case IDs: `submit-button`, `email-input`, `user-list`
- Use semantic Playwright locators (`getByRole`, `getByLabel`) when text is stable
- Avoid relying on CSS classes in test selectors

---

## Regenerating API types

```bash
pnpm generate:api
```

This overwrites `app/shared/types/schema.ts` from the backend OpenAPI spec. Do not edit that file manually.
