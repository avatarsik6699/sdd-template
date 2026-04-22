import { expect, test as base } from '@playwright/test';
import type { Page } from '@playwright/test';

export const ADMIN_EMAIL = 'admin@example.com';
export const ADMIN_PASSWORD = 'changeme123';

type TestFixtures = {
  uniqueEmail: string;
};

export const test = base.extend<TestFixtures>({
  uniqueEmail: async ({}, use, testInfo) => {
    const slug = `${testInfo.workerIndex}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
    await use(`e2e-${slug}@example.com`);
  },
});

export const unauthenticatedStorageState = { cookies: [], origins: [] };

export async function waitForAppReady(page: Page): Promise<void> {
  await page.waitForFunction(() => document.documentElement.dataset.appReady === 'true');
}

export async function loginThroughUi(
  page: Page,
  email = ADMIN_EMAIL,
  password = ADMIN_PASSWORD
): Promise<void> {
  await page.goto('/login');
  await waitForAppReady(page);
  await expect(page.getByTestId('login-submit')).toBeVisible();
  await page.getByTestId('email-input').fill(email);
  await page.getByTestId('password-input').fill(password);
  const loginResponsePromise = page.waitForResponse(
    (response) =>
      response.url().includes('/api/v1/auth/login') && response.request().method() === 'POST'
  );
  await page.getByTestId('login-submit').click();
  const loginResponse = await loginResponsePromise;
  expect(loginResponse.ok()).toBeTruthy();
  await expect(page).toHaveURL(/\/dashboard$/, { timeout: 15_000 });
}

export { expect };
