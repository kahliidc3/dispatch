import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

test.describe("Suppression UI", () => {
  test("suppression page loads", async ({ page }) => {
    await page.goto("/suppression");
    await expect(
      page.getByRole("heading", { name: "Suppression list" }),
    ).toBeVisible();
  });

  test("shows suppression table", async ({ page }) => {
    await page.goto("/suppression");
    await expect(
      page.getByRole("table", { name: "Suppression list" }),
    ).toBeVisible();
  });

  test("emails are masked by default", async ({ page }) => {
    await page.goto("/suppression");
    // Hard bounce entry — raw email should NOT appear, masked should
    await expect(page.getByText("ha**********@example.com")).toBeVisible();
  });

  test("shows reason badges", async ({ page }) => {
    await page.goto("/suppression");
    await expect(page.getByText("Hard bounce").first()).toBeVisible();
  });

  test("shows SES sync panel", async ({ page }) => {
    await page.goto("/suppression");
    await expect(page.getByText("SES suppression sync")).toBeVisible();
  });

  test("shows drift badge when driftCount > 0", async ({ page }) => {
    await page.goto("/suppression");
    await expect(page.getByText("2 drifts")).toBeVisible();
  });

  test("filter by reason narrows table", async ({ page }) => {
    await page.goto("/suppression");
    await page.getByRole("combobox", { name: "Filter by reason" }).selectOption("hard_bounce");
    await expect(page.getByText("Hard bounce").first()).toBeVisible();
    // Should show only hard bounce count
    const hardBounceEntries = 6; // known from mock data
    await expect(page.getByText(`${hardBounceEntries} entries`)).toBeVisible();
  });

  test("search filters by email content", async ({ page }) => {
    await page.goto("/suppression");
    await page.getByRole("searchbox", { name: "Search by email" }).fill("acme.com");
    await expect(page.getByText(/2 entr/)).toBeVisible();
  });

  test("Add entry button opens dialog", async ({ page }) => {
    await page.goto("/suppression");
    await page.getByRole("button", { name: "Add entry" }).click();
    await expect(
      page.getByRole("dialog", { name: "Add suppression entry" }),
    ).toBeVisible();
  });

  test("add dialog submit disabled without email", async ({ page }) => {
    await page.goto("/suppression");
    await page.getByRole("button", { name: "Add entry" }).click();
    await expect(page.getByRole("button", { name: "Add" })).toBeDisabled();
  });

  test("Bulk add button opens dialog", async ({ page }) => {
    await page.goto("/suppression");
    await page.getByRole("button", { name: "Bulk add" }).click();
    await expect(
      page.getByRole("dialog", { name: "Bulk add suppression entries" }),
    ).toBeVisible();
  });

  test("bulk add shows parsed count", async ({ page }) => {
    await page.goto("/suppression");
    await page.getByRole("button", { name: "Bulk add" }).click();
    await page
      .getByLabel("Email addresses")
      .fill("a@example.com\nb@example.com");
    await expect(page.getByText("2 valid addresses parsed")).toBeVisible();
  });

  test("pagination shows when more than 20 entries", async ({ page }) => {
    await page.goto("/suppression");
    await expect(page.getByRole("button", { name: "Next" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Previous" })).toBeDisabled();
  });

  test("next page button navigates forward", async ({ page }) => {
    await page.goto("/suppression");
    await page.getByRole("button", { name: "Next" }).click();
    await expect(page.getByRole("button", { name: "Previous" })).toBeEnabled();
  });

  test("Export CSV button is visible", async ({ page }) => {
    await page.goto("/suppression");
    await expect(
      page.getByRole("button", { name: "Export CSV" }),
    ).toBeVisible();
  });

  test("suppression page — a11y", async ({ page }) => {
    await page.goto("/suppression");
    const results = await new AxeBuilder({ page }).analyze();
    expect(results.violations).toHaveLength(0);
  });
});
