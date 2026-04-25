# Frontend

React 19 + React Router framework mode with SSR, organized as Feature-Sliced Design (FSD).

## UI baseline

- Component system: `shadcn/ui` (Radix base, open-code components in repo)
- Styling/theming: Tailwind CSS v4 + CSS variables
- Dark mode: `next-themes` (`class` strategy)
- Internationalization: `i18next` + `react-i18next`
- Server state: `@tanstack/react-query`

## Layout

```text
frontend/
├── app/
│   ├── root.tsx                # RR7 root layout
│   ├── routes.ts               # RR7 route registry (do not edit)
│   ├── routes/                 # Thin stubs: meta() export + delegate to pages/
│   ├── pages/                  # FSD: full page compositions
│   ├── widgets/                # FSD: composite UI blocks
│   ├── features/               # FSD: feature slices
│   ├── entities/               # FSD: business entities
│   ├── shared/                 # FSD: API, libs, shared ui
│   ├── components/ui/          # shadcn/ui local component primitives
│   ├── lib/                    # shadcn shared utilities
│   └── styles/app.css          # global styles + tailwind imports + theme tokens
├── public/
├── scripts/
├── tests/
├── components.json             # shadcn registry/project config
├── react-router.config.ts      # do not edit
├── vite.config.ts
└── playwright.config.ts
```

## Commands

```bash
pnpm install
pnpm dev
pnpm typecheck
pnpm test
pnpm test:e2e:lint
pnpm test:e2e --project=chromium
pnpm build
pnpm start
```

## shadcn / AI workflow

```bash
# Initialize/update shadcn project wiring
pnpm dlx shadcn@latest init --template react-router

# Add UI primitives
pnpm dlx shadcn@latest add button card input label

# Useful for agent context/debug
pnpm dlx shadcn@latest info --json
pnpm dlx shadcn@latest docs button
pnpm dlx shadcn@latest search @shadcn -q "login form"

# Optional: install shadcn skill into the current coding environment
pnpm dlx skills add shadcn/ui
```

## Conventions

- Route modules under `app/routes/` are thin stubs. They export `meta()` and delegate rendering to `app/pages/`.
- Never put business logic or heavy JSX in route modules.
- FSD import rule: `routes → pages → widgets → features → entities → shared`.
- Use aliases for cross-layer imports: `@pages/`, `@widgets/`, `@features/`, `@entities/`, `@shared/`.
- For shadcn internals, use `@/components/*` and `@/lib/*`.
- `app/routes.ts` and `react-router.config.ts` must not be edited as part of FSD work.
- Use Playwright CLI only for explicit manual debugging requests; keep gate automation deterministic.
