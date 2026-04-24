# Frontend

React 19 + React Router framework mode with server-side rendering.

The frontend is intentionally minimal: it proves that the template system works with a non-Vue
SSR stack while keeping enough real structure for routing, metadata, and gate commands.

## Layout

```text
frontend/
├── app/
│   ├── root.tsx
│   ├── routes.ts
│   ├── routes/
│   │   ├── home.tsx
│   │   └── login.tsx
│   └── styles/app.css
├── public/
├── scripts/
├── tests/
│   ├── home.test.ts
│   └── e2e/home.spec.ts
├── react-router.config.ts
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
pnpm playwright:cli -- open http://localhost:3000 --headed
cd ..
./scripts/install-caveman.sh
pnpm build
pnpm start
```

## Conventions

- Keep route modules under `app/routes/`.
- Put document metadata in route-level `meta()` exports.
- Use SSR-safe rendering only in route modules and `root.tsx`.
- Prefer simple CSS in `app/styles/app.css`; this template does not depend on Tailwind.
- Use Playwright CLI only for explicit manual debugging requests; keep gate automation on deterministic Playwright test commands.
- Use Caveman only as an explicit opt-in response compression mode (`./scripts/install-caveman.sh` + `/caveman` or `$caveman`), not as default project policy.
