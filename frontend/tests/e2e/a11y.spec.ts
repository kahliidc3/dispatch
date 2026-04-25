import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";
import { signInToShell, startSignIn } from "./support/session";

test("has no detected accessibility violations on /login", async ({ page }) => {
  await page.goto("/login");

  const results = await new AxeBuilder({ page }).analyze();
  expect(results.violations).toEqual([]);
});

test("has no detected accessibility violations on /mfa", async ({ page }) => {
  await startSignIn(page);

  const results = await new AxeBuilder({ page }).analyze();
  expect(results.violations).toEqual([]);
});

test("has no detected accessibility violations on /settings/api-keys", async ({
  page,
}) => {
  await signInToShell(page);
  await page.goto("/settings/api-keys");

  const results = await new AxeBuilder({ page }).analyze();
  expect(results.violations).toEqual([]);
});
