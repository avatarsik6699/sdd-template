import { expect, test } from "@playwright/test";

test("home page renders the SSR headline", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "[PROJECT_NAME]" })).toBeVisible();
});
