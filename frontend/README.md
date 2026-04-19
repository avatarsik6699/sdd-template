# Frontend Testing Guidelines

This project uses **Playwright** for end-to-end (E2E) testing and **Vitest** for unit/component testing. This document provides guidelines to ensure our frontend components remain highly testable, stable, and maintainable.

## E2E Testing with Playwright

Playwright is configured to run tests against our Dockerized application.

### Running Tests

Ensure your Docker environment is up and running before running the E2E tests:

```bash
# In the root directory:
docker-compose up -d
```

Then run the tests from the `frontend/` directory:

```bash
# Install playwright browsers (first time only)
pnpm test:e2e:install

# Run tests headlessly
pnpm test:e2e

# Run tests with the UI runner (great for debugging)
pnpm test:e2e:ui
```

> **Note:** By default, Playwright connects to `http://localhost:3000`. You can change this by setting `PLAYWRIGHT_BASE_URL` (e.g., `PLAYWRIGHT_BASE_URL=http://localhost pnpm test:e2e` to hit the Nginx gateway).

---

## Guidelines for Writing Testable Components

To ensure UI changes do not break tests, we follow these best practices for element selection and component structure.

### 1. Use `data-testid` for Selecting Elements

**Do not** rely on CSS classes, element IDs, or complex DOM hierarchies for test selections. These are prone to change during styling updates and refactoring.

Instead, add a `data-testid` attribute to elements that need to be interacted with or asserted in tests.

**Bad:**
```vue
<button class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
  Submit
</button>
<!-- Playwright: await page.locator('.bg-blue-500').click() -->
```

**Good:**
```vue
<button data-testid="submit-button" class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
  Submit
</button>
<!-- Playwright: await page.getByTestId('submit-button').click() -->
```

### 2. Standardize `data-testid` Naming Conventions

Use consistent, descriptive kebab-case names for test IDs:
- `{action}-button`: `submit-button`, `cancel-button`, `delete-user-button`
- `{entity}-list`: `user-list`, `product-list`
- `{field}-input`: `email-input`, `password-input`
- `{context}-{element}`: `login-form-submit`, `header-nav-login`

### 3. Favor User-Facing Locators Where Appropriate

While `data-testid` is the most resilient fallback, Playwright recommends using user-facing attributes where semantic HTML is properly used.

- `getByRole('button', { name: 'Submit' })`
- `getByLabel('Password')`
- `getByPlaceholder('Search...')`

**Rule of Thumb:** If the text/role is core to the feature and rarely changes (e.g., a "Log in" button or "Email" label), use semantic locators (`getByRole`, `getByLabel`). If the element lacks text, or the text changes often based on i18n, use `data-testid`.

### 4. Keep Components Isolated and Deterministic

- **Mock external dependencies** in unit tests where possible.
- E2E tests should use deterministic data. Run E2E tests against an isolated test database or use predictable seeds.
- Avoid relying on precise timeouts. Use Playwright's auto-waiting features (`await expect(page.getByTestId('loading-spinner')).toBeHidden()`).

### 5. Expose State for Tests (If Necessary)

Sometimes you need to know if a Nuxt app has finished hydrating. Nuxt and Vue usually handle this seamlessly, but avoid animations blocking test interactions. Playwright automatically waits for actionability, but you can disable animations in tests via CSS if they cause flakiness.

```css
/* Example: Disable animations during tests */
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

(Playwright handles this well natively, but it's good to keep in mind for heavy UI transitions.)
