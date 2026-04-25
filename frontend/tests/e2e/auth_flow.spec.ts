import { expect, test } from "@playwright/test";
import { completeMfa, startSignIn } from "./support/session";

test("supports login, MFA, dashboard, and logout round trip", async ({ page }) => {
  await startSignIn(page);
  await completeMfa(page);

  await expect(page).toHaveURL(/\/$/);
  await expect(
    page.getByRole("heading", {
      name: "Dispatch",
    }),
  ).toBeVisible();

  await page.getByRole("button", { name: /operator/i }).click();
  await page.getByRole("menuitem", { name: "Sign out" }).click();

  await expect(page).toHaveURL(/\/login$/);
  await expect(page.getByRole("heading", { name: "Sign in" })).toBeVisible();
});

test("rate-limits invalid MFA without exposing attempt counts", async ({ page }) => {
  await startSignIn(page);

  for (let index = 0; index < 2; index += 1) {
    await completeMfa(page, "111111");
    await expect(
      page.getByText("Code not accepted. Try a fresh code from your authenticator app."),
    ).toBeVisible();
    await expect(page.getByLabel("Six-digit code")).toHaveValue("");
  }

  await completeMfa(page, "111111");
  await expect(
    page.getByText("Verification unavailable - start again."),
  ).toBeVisible();
  await expect(page.getByText(/attempt/i)).toHaveCount(0);
});
