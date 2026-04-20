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

### Style & lint

- **ESLint** — flat config in [eslint.config.mjs](eslint.config.mjs). Vue + TypeScript rules, Prettier runs last to resolve formatting conflicts.
- **Prettier** — config in [.prettierrc](.prettierrc): 100-char lines, single quotes, trailing commas `es5`.
- **TypeScript strictness** is delegated to Nuxt-generated `tsconfig.json`. Do not hand-roll a replacement.

Before committing:

```bash
pnpm lint:fix
pnpm nuxt prepare
pnpm typecheck
```

### TypeScript / Vue patterns

- **`<script setup lang="ts">` only.** No Options API. No `defineComponent` wrappers.
- **Typed API fetching** via the generic `useApiFetch<Path, Method>` composable from [app/shared/api/use-api-fetch.ts](app/shared/api/use-api-fetch.ts). Don't call `$fetch` raw in components — you lose path/response typing from the OpenAPI schema.
- **Pinia stores** use `defineStore('namespace/name', () => { ... })` setup syntax. Example: [app/features/auth/model/auth-store.ts](app/features/auth/model/auth-store.ts).
- **Namespace typing pattern** (for module-grouped helpers): see [app/shared/lib/safe-cookie.ts](app/shared/lib/safe-cookie.ts) — exports both the namespace and the functions so consumers can import either style.
- **i18n keys** live in [i18n/locales/en.json](i18n/locales/en.json) / [i18n/locales/ru.json](i18n/locales/ru.json). Never hardcode user-facing strings in `.vue` templates.

### Auto-imports

Nuxt auto-imports the following (configured in [nuxt.config.ts](nuxt.config.ts)). When editing files, **omit the import** for anything in these dirs — adding an explicit import causes an ESLint auto-import conflict:

| Source | What's auto-imported |
|--------|----------------------|
| `app/shared/api/` | composables (e.g. `useApiFetch`) |
| `app/shared/lib/` | utilities (e.g. `safeCookie`) |
| `app/shared/model/` | shared Pinia stores (e.g. `useUiStore`) |
| `app/features/auth/model/` | auth store (`useAuthStore`) |
| `app/widgets/**` | Vue components — use them as `<SidebarNav />` without imports |

Nuxt's own `defineNuxtConfig`, `ref`, `computed`, `useRoute`, etc. are also auto-imported via Nuxt's built-in module — do not import them explicitly.

---

## Testing

### Unit tests (Vitest)

```bash
pnpm nuxt prepare
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

### E2E expectations (gate requirement)

The `/phase-gate` skill requires a ✅ e2e row before commit — unit tests alone do NOT clear the gate.

- **One spec per user-facing flow** introduced in the phase. Specs live under [tests/e2e/](tests/e2e/).
- **Run against the full Docker stack** — `db`, `redis`, `backend`, `frontend`, `nginx` must all be healthy. The gate skill will refuse to run Playwright otherwise; it does NOT auto-start the stack.
- **Reporter config** is pinned in [playwright.config.ts](playwright.config.ts) to emit three outputs: `list` (CLI), `html` (clickable report), and `junit` at `test-results/junit.xml` (parsed by the gate skill).
- **Debugging a failure**: open `playwright-report/index.html`, or run with the inspector: `pnpm test:e2e:ui`.
- **Test IDs are kebab-case** to match the `testIdAttribute: 'data-testid'` config.

---

## Mandatory rules (duplicated locally — these are load-bearing)

Repeated here because an AI editing inside [app/](app/) (frontend Nuxt app) often won't open the root [../AGENTS.md](../AGENTS.md) or [../CLAUDE.md](../CLAUDE.md), and missing either of these burns tokens.

1. **Use up-to-date docs before writing code against any external library** — Nuxt, Vue, Pinia, Tailwind, Nuxt UI, Vitest, Playwright, @nuxtjs/i18n, or any third-party package. Prefer a configured docs MCP such as Context7 when available, then `ctx7` CLI, then official docs. Full rule in [../AGENTS.md](../AGENTS.md#documentation-lookup), [../CLAUDE.md](../CLAUDE.md#library-documentation-lookup-mandatory), and [../docs/AGENT_SETUP.md](../docs/AGENT_SETUP.md).

2. **On `EACCES` / `EPERM` / "Permission denied"** (most often on `.nuxt/`, `.output/`, or `node_modules/.cache/` after a Docker run) — stop immediately, post the handoff message from [../CLAUDE.md](../CLAUDE.md#filesystem-permission-failures--stop-and-ask) to the user with the real path, wait for the keyword `continue` before retrying. Never `sudo`, `chmod`, or loop.

---

## Regenerating API types

```bash
pnpm generate:api
```

This overwrites `app/shared/types/schema.ts` from the backend OpenAPI spec. Do not edit that file manually.
