import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

test.describe("Public unsubscribe page", () => {
  test("shows invalid link message when no token", async ({ page }) => {
    await page.goto("/unsubscribe");
    await expect(
      page.getByText(/invalid or has expired/i),
    ).toBeVisible();
  });

  test("shows confirm button when token is present", async ({ page }) => {
    await page.goto("/unsubscribe?t=some-token-value");
    await expect(
      page.getByRole("heading", { name: /confirm unsubscribe/i }),
    ).toBeVisible();
    await expect(
      page.getByRole("button", { name: /unsubscribe/i }),
    ).toBeVisible();
  });

  test("page has noindex meta robots", async ({ page }) => {
    await page.goto("/unsubscribe");
    const robots = await page
      .locator('meta[name="robots"]')
      .getAttribute("content");
    expect(robots).toMatch(/noindex/i);
  });

  test("unsubscribe page — a11y (no token)", async ({ page }) => {
    await page.goto("/unsubscribe");
    const results = await new AxeBuilder({ page }).analyze();
    expect(results.violations).toHaveLength(0);
  });

  test("unsubscribe page — a11y (with token)", async ({ page }) => {
    await page.goto("/unsubscribe?t=test-token");
    const results = await new AxeBuilder({ page }).analyze();
    expect(results.violations).toHaveLength(0);
  });
});
