import { expect, test } from "@playwright/test";

test("home page renders the SSR headline", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "[PROJECT_NAME]" })).toBeVisible();
  await expect(page.getByRole("button", { name: "EN" })).toBeVisible();
  await expect(page.getByRole("button", { name: "RU" })).toBeVisible();
  await expect(page.getByRole("button", { name: "light" })).toBeVisible();
  await expect(page.getByRole("button", { name: "dark" })).toBeVisible();
  await expect(page.getByRole("button", { name: "system" })).toBeVisible();
});
