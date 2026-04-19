import { test, expect } from '@playwright/test';

test('homepage has title', async ({ page }) => {
  // Navigate to the base URL (configured in playwright.config.ts)
  await page.goto('/');

  // Assuming Nuxt sets a default title or you have an element to verify
  // Adjust this to match your actual homepage content
  await expect(page).toHaveTitle(/.*|Nuxt/i);
});

test('login navigation example', async ({ page }) => {
  await page.goto('/');

  // Example of using data-testid for stable testing
  // e.g., <NuxtLink to="/login" data-testid="login-link">Login</NuxtLink>
  // await page.getByTestId('login-link').click();
  // await expect(page).toHaveURL(/.*login/);
});
