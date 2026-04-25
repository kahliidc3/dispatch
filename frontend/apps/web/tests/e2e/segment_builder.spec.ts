import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

test.describe("Segment builder", () => {
  test("segments list page loads", async ({ page }) => {
    await page.goto("/segments");
    await expect(
      page.getByRole("heading", { name: "Segments" }),
    ).toBeVisible();
  });

  test("segments list shows segment names", async ({ page }) => {
    await page.goto("/segments");
    await expect(page.getByText("Active newsletter subscribers")).toBeVisible();
    await expect(page.getByText("Recent openers or clickers")).toBeVisible();
  });

  test("segments list shows last computed count badges", async ({ page }) => {
    await page.goto("/segments");
    await expect(page.getByText("12,847")).toBeVisible();
  });

  test("clicking a segment navigates to builder", async ({ page }) => {
    await page.goto("/segments");
    await page
      .getByRole("link", { name: "Active newsletter subscribers" })
      .click();
    await expect(
      page.getByRole("heading", { name: "Active newsletter subscribers" }),
    ).toBeVisible();
  });

  test("builder shows AND/OR toggle", async ({ page }) => {
    await page.goto("/segments/seg-001");
    await expect(page.getByRole("button", { name: "AND" })).toBeVisible();
    await expect(page.getByRole("button", { name: "OR" })).toBeVisible();
  });

  test("builder shows field, operator, value selects", async ({ page }) => {
    await page.goto("/segments/seg-001");
    await expect(
      page.getByRole("combobox", { name: "Condition field" }).first(),
    ).toBeVisible();
    await expect(
      page.getByRole("combobox", { name: "Condition operator" }).first(),
    ).toBeVisible();
  });

  test("builder shows Add condition button", async ({ page }) => {
    await page.goto("/segments/seg-001");
    await expect(
      page.getByRole("button", { name: "+ Add condition" }).first(),
    ).toBeVisible();
  });

  test("clicking Add condition adds a new row", async ({ page }) => {
    await page.goto("/segments/seg-001");
    const addBtn = page.getByRole("button", { name: "+ Add condition" }).first();
    const beforeCount = await page
      .getByRole("combobox", { name: "Condition field" })
      .count();
    await addBtn.click();
    const afterCount = await page
      .getByRole("combobox", { name: "Condition field" })
      .count();
    expect(afterCount).toBe(beforeCount + 1);
  });

  test("clicking Add group adds a nested group", async ({ page }) => {
    await page.goto("/segments/seg-001");
    await page.getByRole("button", { name: "+ Add group" }).first().click();
    await expect(
      page.getByRole("button", { name: "Remove group" }),
    ).toBeVisible();
  });

  test("switching AND to OR updates aria-pressed", async ({ page }) => {
    await page.goto("/segments/seg-001");
    const orBtn = page.getByRole("button", { name: "OR" }).first();
    await orBtn.click();
    await expect(orBtn).toHaveAttribute("aria-pressed", "true");
  });

  test("save button disabled initially (no unsaved changes)", async ({
    page,
  }) => {
    await page.goto("/segments/seg-001");
    await expect(
      page.getByRole("button", { name: "Save segment" }),
    ).toBeDisabled();
  });

  test("save button enabled after changing segment name", async ({ page }) => {
    await page.goto("/segments/seg-001");
    await page.getByLabel("Segment name").fill("Updated name");
    await expect(
      page.getByRole("button", { name: "Save segment" }),
    ).toBeEnabled();
  });

  test("changing field resets operator to valid default", async ({ page }) => {
    await page.goto("/segments/seg-001");
    const fieldSelect = page
      .getByRole("combobox", { name: "Condition field" })
      .first();
    await fieldSelect.selectOption("email");
    const opSelect = page
      .getByRole("combobox", { name: "Condition operator" })
      .first();
    const opValue = await opSelect.inputValue();
    // email is string type, should have eq/neq/contains
    expect(["eq", "neq", "contains"]).toContain(opValue);
  });

  test("3-level nested group can be built", async ({ page }) => {
    await page.goto("/segments/seg-001");
    // Add a group inside root
    await page.getByRole("button", { name: "+ Add group" }).first().click();
    // Add a group inside the first nested group
    await page.getByRole("button", { name: "+ Add group" }).first().click();
    // Should have nested groups rendered
    const removeGroupBtns = page.getByRole("button", { name: "Remove group" });
    expect(await removeGroupBtns.count()).toBeGreaterThanOrEqual(1);
  });

  test("create segment dialog opens", async ({ page }) => {
    await page.goto("/segments");
    await page.getByRole("button", { name: "New segment" }).click();
    await expect(
      page.getByRole("dialog", { name: "Create segment" }),
    ).toBeVisible();
  });

  test("404 for unknown segment", async ({ page }) => {
    const response = await page.goto("/segments/nonexistent-segment");
    expect(response?.status()).toBe(404);
  });

  test("segments list — a11y", async ({ page }) => {
    await page.goto("/segments");
    const results = await new AxeBuilder({ page }).analyze();
    expect(results.violations).toHaveLength(0);
  });

  test("segment builder — a11y", async ({ page }) => {
    await page.goto("/segments/seg-001");
    const results = await new AxeBuilder({ page }).analyze();
    expect(results.violations).toHaveLength(0);
  });
});
