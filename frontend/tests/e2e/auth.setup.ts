import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { test as setup } from '@playwright/test';
import { loginThroughUi } from './fixtures';

const authFile = path.join(path.dirname(fileURLToPath(import.meta.url)), '.auth/admin.json');

setup('authenticate admin session', async ({ page }) => {
  await loginThroughUi(page);
  await page.context().storageState({ path: authFile });
});
