import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

test.describe("CSV import wizard", () => {
  test("import page loads with upload step", async ({ page }) => {
    await page.goto("/contacts/import");
    await expect(
      page.getByRole("heading", { name: "Import contacts" }),
    ).toBeVisible();
    await expect(
      page.getByRole("button", { name: /drop zone/i }),
    ).toBeVisible();
  });

  test("wizard nav shows all four steps", async ({ page }) => {
    await page.goto("/contacts/import");
    const nav = page.getByRole("navigation", { name: "Import wizard steps" });
    await expect(nav.getByText("Upload")).toBeVisible();
    await expect(nav.getByText("Column mapping")).toBeVisible();
    await expect(nav.getByText("Progress")).toBeVisible();
    await expect(nav.getByText("Review errors")).toBeVisible();
  });

  test("upload step shows 25 MB size limit", async ({ page }) => {
    await page.goto("/contacts/import");
    await expect(page.getByText(/25 MB/)).toBeVisible();
  });

  test("uploading a valid CSV shows column mapping", async ({ page }) => {
    await page.goto("/contacts/import");
    const csvContent = "email,first_name,last_name\nalice@example.com,Alice,Smith\nbob@example.com,Bob,Jones";
    const buffer = Buffer.from(csvContent);
    const [fileChooser] = await Promise.all([
      page.waitForEvent("filechooser"),
      page.getByRole("button", { name: /drop zone/i }).click(),
    ]);
    await fileChooser.setFiles({
      name: "contacts.csv",
      mimeType: "text/csv",
      buffer,
    });
    await expect(page.getByText("contacts.csv")).toBeVisible();
    await expect(page.getByText(/3 column/)).toBeVisible();
    await expect(page.getByText("Preview")).toBeVisible();
  });

  test("proceeding to mapping shows column selects", async ({ page }) => {
    await page.goto("/contacts/import");
    const csvContent = "email,first_name,phone\nalice@example.com,Alice,555-1234";
    const buffer = Buffer.from(csvContent);
    const [fileChooser] = await Promise.all([
      page.waitForEvent("filechooser"),
      page.getByRole("button", { name: /drop zone/i }).click(),
    ]);
    await fileChooser.setFiles({
      name: "contacts.csv",
      mimeType: "text/csv",
      buffer,
    });
    await page.getByRole("button", { name: /continue to column mapping/i }).click();
    await expect(
      page.getByRole("combobox", { name: 'Map column "email"' }),
    ).toBeVisible();
    await expect(
      page.getByRole("combobox", { name: 'Map column "first_name"' }),
    ).toBeVisible();
  });

  test("email auto-detected as email field", async ({ page }) => {
    await page.goto("/contacts/import");
    const csvContent = "email,company\nalice@example.com,Acme";
    const buffer = Buffer.from(csvContent);
    const [fileChooser] = await Promise.all([
      page.waitForEvent("filechooser"),
      page.getByRole("button", { name: /drop zone/i }).click(),
    ]);
    await fileChooser.setFiles({
      name: "contacts.csv",
      mimeType: "text/csv",
      buffer,
    });
    await page.getByRole("button", { name: /continue to column mapping/i }).click();
    const emailSelect = page.getByRole("combobox", {
      name: 'Map column "email"',
    });
    await expect(emailSelect).toHaveValue("email");
  });

  test("upload page — a11y", async ({ page }) => {
    await page.goto("/contacts/import");
    const results = await new AxeBuilder({ page }).analyze();
    expect(results.violations).toHaveLength(0);
  });

  test("non-csv file shows error", async ({ page }) => {
    await page.goto("/contacts/import");
    const [fileChooser] = await Promise.all([
      page.waitForEvent("filechooser"),
      page.getByRole("button", { name: /drop zone/i }).click(),
    ]);
    await fileChooser.setFiles({
      name: "data.xlsx",
      mimeType: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
      buffer: Buffer.from("fake xlsx"),
    });
    await expect(page.getByRole("alert")).toContainText(/only .csv/i);
  });
});
