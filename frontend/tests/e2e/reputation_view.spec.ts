import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

test.describe("Domain reputation view", () => {
  test("reputation page loads", async ({ page }) => {
    await page.goto("/analytics/reputation");
    await expect(
      page.getByRole("heading", { name: "Domain reputation" }),
    ).toBeVisible();
  });

  test("shows freshness indicator", async ({ page }) => {
    await page.goto("/analytics/reputation");
    await expect(page.getByText(/last updated/i)).toBeVisible();
  });

  test("shows threshold legend", async ({ page }) => {
    await page.goto("/analytics/reputation");
    await expect(page.getByText(/0\.75%/)).toBeVisible();
    await expect(page.getByText(/1\.5%/)).toBeVisible();
  });

  test("renders domain table with all columns", async ({ page }) => {
    await page.goto("/analytics/reputation");
    await expect(page.getByText("Bounce%")).toBeVisible();
    await expect(page.getByText("Complaint%")).toBeVisible();
    await expect(page.getByText("Delivery%")).toBeVisible();
    await expect(page.getByText("Breaker")).toBeVisible();
    await expect(page.getByText("Warmup stage")).toBeVisible();
    await expect(page.getByText("Risk")).toBeVisible();
  });

  test("shows all 3 domains", async ({ page }) => {
    await page.goto("/analytics/reputation");
    await expect(page.getByText("m48.dispatch.internal")).toBeVisible();
    await expect(page.getByText("m49.dispatch.internal")).toBeVisible();
    await expect(page.getByText("m47.dispatch.internal")).toBeVisible();
  });

  test("critical domain has critical badge", async ({ page }) => {
    await page.goto("/analytics/reputation");
    await expect(page.getByText("critical")).toBeVisible();
  });

  test("open breaker has open badge", async ({ page }) => {
    await page.goto("/analytics/reputation");
    await expect(page.getByText("open").first()).toBeVisible();
  });

  test("domain name links to domain detail page", async ({ page }) => {
    await page.goto("/analytics/reputation");
    const link = page.getByRole("link", { name: /m48\.dispatch\.internal/ });
    await expect(link).toHaveAttribute("href", "/domains/dom-002");
  });

  test("no accessibility violations", async ({ page }) => {
    await page.goto("/analytics/reputation");
    const results = await new AxeBuilder({ page }).analyze();
    expect(results.violations).toHaveLength(0);
  });
});
