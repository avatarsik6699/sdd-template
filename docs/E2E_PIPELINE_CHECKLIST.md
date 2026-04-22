# E2E Pipeline Checklist (Playwright)

Use this checklist when bootstrapping CI and branch-protection rules in projects created from this template.

## Required PR gate

- [ ] Use `CI` workflow as the single required PR path for E2E.
- [ ] Require job/check name `E2E (Chromium)` in branch protection.
- [ ] Keep Chromium as the only pass/fail browser for required checks.
- [ ] Keep cross-browser runs (`pnpm test:e2e:all`) optional and non-gating unless explicitly upgraded by project policy.

## Deterministic execution contract

- [ ] Start full Docker stack before E2E (`db`, `redis`, `backend`, `frontend`, `nginx`).
- [ ] Wait for health/readiness and warm endpoints before Playwright starts.
- [ ] Run migrations before E2E.
- [ ] Run E2E anti-flake lint before E2E execution: `pnpm test:e2e:lint`.
- [ ] Run required command path: `pnpm test:e2e --project=chromium`.

## Performance baseline

- [ ] Keep pnpm cache enabled via `actions/setup-node` (`cache: pnpm`).
- [ ] Use `pnpm install --frozen-lockfile --prefer-offline`.
- [ ] Build Docker images with Buildx GHA cache (`cache-from/to: type=gha`) and start compose with `--no-build`.
- [ ] Avoid duplicate dependency-install steps in the E2E job.

## Failure diagnostics contract

- [ ] Upload `frontend/playwright-report` artifact.
- [ ] Upload `frontend/test-results` (JUnit + traces) artifact.
- [ ] Emit timing summary in CI logs (install/build/readiness/test durations).
- [ ] Triage failures from artifacts first (HTML report, JUnit, traces) before modifying tests.

## Test authoring rules

- [ ] Prefer `getByRole`, `getByLabel`, `getByTestId` locators.
- [ ] Use web-first assertions (`await expect(...)`) for readiness and state.
- [ ] Do not commit `waitForTimeout(...)` in E2E tests.
- [ ] Keep login-flow assertions explicit; use setup-generated `storageState` for post-auth flows.
- [ ] Ensure test data is isolated per test and independent of leftovers or order.
