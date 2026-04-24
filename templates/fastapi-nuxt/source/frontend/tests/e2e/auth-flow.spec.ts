import {
  expect,
  loginThroughUi,
  test,
  unauthenticatedStorageState,
  waitForAppReady,
} from './fixtures';

test.describe('auth baseline flow', () => {
  test.describe('unauthenticated routes and login', () => {
    test.use({ storageState: unauthenticatedStorageState });

    test('redirects unauthenticated dashboard visits to login', async ({ page }) => {
      await page.goto('/dashboard');
      await expect(page).toHaveURL(/\/login$/);
      await expect(page.getByTestId('login-submit')).toBeVisible();
    });

    test('signs in on first click', async ({ page }) => {
      await loginThroughUi(page);
      await expect(page.getByTestId('dashboard-shell')).toBeVisible();
      await expect(page.getByTestId('user-email')).toContainText('admin@example.com');
    });

    test('shows error for invalid credentials', async ({ page, uniqueEmail }) => {
      await page.goto('/login');
      await waitForAppReady(page);
      await expect(page.getByTestId('login-submit')).toBeVisible();
      await page.getByTestId('email-input').fill(uniqueEmail);
      await page.getByTestId('password-input').fill('wrong-password');
      await page.getByTestId('login-submit').click();

      await expect(page).toHaveURL(/\/login$/);
      await expect(page.getByTestId('login-error')).toHaveText(
        'Invalid email or password. Please try again.'
      );
    });
  });

  test('logs out and blocks returning to dashboard', async ({ page }) => {
    await page.goto('/dashboard');
    await expect(page).toHaveURL(/\/dashboard$/);
    await expect(page.getByTestId('logout-button')).toBeVisible();

    await page.getByTestId('logout-button').click();
    await expect(page).toHaveURL(/\/login$/);

    await page.goto('/dashboard');
    await expect(page).toHaveURL(/\/login$/);
  });
});
