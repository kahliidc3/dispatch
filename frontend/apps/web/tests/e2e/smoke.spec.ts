import { expect, test } from "@playwright/test";
import { signInToShell } from "./support/session";

test("renders the login placeholder", async ({ page }) => {
  await page.goto("/login");

  await expect(
    page.getByRole("heading", {
      name: "Sign in",
    }),
  ).toBeVisible();
  await expect(page.getByLabel("Email")).toBeVisible();
  await expect(page.getByLabel("Password")).toBeVisible();
  await expect(
    page.getByRole("button", {
      name: "Continue to verification",
    }),
  ).toBeVisible();
});

test("renders the protected dashboard shell after local sign-in", async ({
  page,
}) => {
  await signInToShell(page);

  await expect(page.getByText("Core shell foundation")).toBeVisible();
  await expect(page.getByRole("navigation", { name: "Primary" })).toBeVisible();
  await expect(page.getByText("Local session", { exact: true })).toBeVisible();
});

test("supports keyboard-only navigation from the command palette", async ({
  page,
}) => {
  await signInToShell(page);

  await page.keyboard.press("Control+K");
  await expect(page.getByRole("dialog")).toBeVisible();

  const searchInput = page.getByLabel("Search routes");
  await searchInput.fill("suppression");
  await searchInput.press("Enter");

  await expect(page).toHaveURL(/\/suppression$/);
  await expect(
    page.getByRole("heading", {
      name: "Suppression",
    }),
  ).toBeVisible();
});
