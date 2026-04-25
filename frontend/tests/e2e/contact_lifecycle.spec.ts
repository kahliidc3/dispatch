import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

test.describe("Contact lifecycle", () => {
  test("contacts list page loads and shows contacts", async ({ page }) => {
    await page.goto("/contacts");
    await expect(page.getByRole("heading", { name: "Contacts" })).toBeVisible();
    await expect(
      page.getByRole("searchbox", { name: /search contacts/i }),
    ).toBeVisible();
  });

  test("contacts list has lifecycle filter", async ({ page }) => {
    await page.goto("/contacts");
    const select = page.getByRole("combobox", { name: /filter by lifecycle/i });
    await expect(select).toBeVisible();
  });

  test("contact detail page loads for ctc-001", async ({ page }) => {
    await page.goto("/contacts/ctc-001");
    await expect(
      page.getByText("founder.alpha@example.com"),
    ).toBeVisible();
    await expect(page.getByRole("tab", { name: "Overview" })).toBeVisible();
    await expect(page.getByRole("tab", { name: /Lists/ })).toBeVisible();
    await expect(
      page.getByRole("tab", { name: "Preferences" }),
    ).toBeVisible();
    await expect(page.getByRole("tab", { name: /History/ })).toBeVisible();
  });

  test("contact detail tabs switch content", async ({ page }) => {
    await page.goto("/contacts/ctc-001");
    await page.getByRole("tab", { name: "Preferences" }).click();
    await expect(page.getByText("Newsletter")).toBeVisible();
  });

  test("suppressed contact shows danger badge on detail", async ({ page }) => {
    await page.goto("/contacts/ctc-002");
    await expect(page.getByText("suppressed")).toBeVisible();
    await expect(page.getByText("Hard bounce on April newsletter")).toBeVisible();
  });

  test("new contact form has required email field", async ({ page }) => {
    await page.goto("/contacts/new");
    await expect(page.getByRole("heading", { name: "Add contact" })).toBeVisible();
    await expect(
      page.getByRole("textbox", { name: /email address/i }),
    ).toBeVisible();
  });

  test("contacts list — a11y", async ({ page }) => {
    await page.goto("/contacts");
    const results = await new AxeBuilder({ page }).analyze();
    expect(results.violations).toHaveLength(0);
  });

  test("contact detail — a11y", async ({ page }) => {
    await page.goto("/contacts/ctc-001");
    const results = await new AxeBuilder({ page }).analyze();
    expect(results.violations).toHaveLength(0);
  });

  test("404 for unknown contact", async ({ page }) => {
    const response = await page.goto("/contacts/ctc-9999");
    expect(response?.status()).toBe(404);
  });
});
