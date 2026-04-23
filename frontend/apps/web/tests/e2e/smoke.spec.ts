import { expect, test } from "@playwright/test";

test("renders the dashboard placeholder", async ({ page }) => {
  await page.goto("/");

  await expect(
    page.getByRole("heading", {
      name: "Dispatch",
    }),
  ).toBeVisible();
  await expect(page.getByText("Docs-first scaffold")).toBeVisible();
});

test("renders the login placeholder", async ({ page }) => {
  await page.goto("/login");

  await expect(
    page.getByRole("heading", {
      name: "Sign in",
    }),
  ).toBeVisible();
  await expect(page.getByLabel("Email")).toBeVisible();
  await expect(page.getByLabel("Password")).toBeVisible();
});
