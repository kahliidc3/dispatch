import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

test.describe("Template editor & versioning", () => {
  test("templates list page loads", async ({ page }) => {
    await page.goto("/templates");
    await expect(
      page.getByRole("heading", { name: "Templates" }),
    ).toBeVisible();
    await expect(page.getByRole("table", { name: "Template list" })).toBeVisible();
  });

  test("templates list shows template names", async ({ page }) => {
    await page.goto("/templates");
    await expect(page.getByText("Warmup plain text")).toBeVisible();
    await expect(page.getByText("Seed inbox check")).toBeVisible();
  });

  test("clicking a template navigates to detail", async ({ page }) => {
    await page.goto("/templates");
    await page.getByRole("link", { name: "Warmup plain text" }).click();
    await expect(
      page.getByRole("heading", { name: "Warmup plain text" }),
    ).toBeVisible();
  });

  test("template detail shows editor tabs", async ({ page }) => {
    await page.goto("/templates/tpl-001");
    await expect(page.getByRole("tab", { name: "Subject" })).toBeVisible();
    await expect(page.getByRole("tab", { name: "Plain text" })).toBeVisible();
    await expect(page.getByRole("tab", { name: "HTML" })).toBeVisible();
  });

  test("subject is pre-filled with active version", async ({ page }) => {
    await page.goto("/templates/tpl-001");
    await expect(page.getByLabel("Subject line")).toHaveValue(
      "Quick check-in, {{first_name}}",
    );
  });

  test("save button is disabled initially", async ({ page }) => {
    await page.goto("/templates/tpl-001");
    await expect(
      page.getByRole("button", { name: /save as new version/i }),
    ).toBeDisabled();
  });

  test("editing subject enables save button", async ({ page }) => {
    await page.goto("/templates/tpl-001");
    await page.getByLabel("Subject line").fill("New subject line");
    await expect(
      page.getByRole("button", { name: /save as new version/i }),
    ).toBeEnabled();
  });

  test("insert merge tag button shows tag list", async ({ page }) => {
    await page.goto("/templates/tpl-001");
    await page.getByRole("button", { name: /insert merge tag/i }).click();
    await expect(
      page.getByRole("listbox", { name: /available merge tags/i }),
    ).toBeVisible();
    await expect(page.getByText("First name")).toBeVisible();
  });

  test("preview pane shows rendered subject", async ({ page }) => {
    await page.goto("/templates/tpl-001");
    await expect(page.getByText(/subject:/i)).toBeVisible();
    await expect(page.getByText("Avery")).toBeVisible();
  });

  test("reset button in preview restores default sample JSON", async ({
    page,
  }) => {
    await page.goto("/templates/tpl-001");
    await page.getByLabel("Sample contact data").fill("{}");
    await page.getByRole("button", { name: "Reset" }).click();
    const textarea = page.getByLabel("Sample contact data");
    await expect(textarea).toContainText("first_name");
  });

  test("show version history toggle opens version list", async ({ page }) => {
    await page.goto("/templates/tpl-001");
    await page
      .getByRole("button", { name: /show version history/i })
      .click();
    await expect(page.getByText("Version history")).toBeVisible();
    await expect(page.getByText("v1")).toBeVisible();
    await expect(page.getByText("v2")).toBeVisible();
  });

  test("active version has Active badge in history", async ({ page }) => {
    await page.goto("/templates/tpl-001");
    await page
      .getByRole("button", { name: /show version history/i })
      .click();
    await expect(page.getByText("Active")).toBeVisible();
  });

  test("preview iframe cannot make outbound network requests", async ({
    page,
  }) => {
    const outboundRequests: string[] = [];
    page.on("request", (req) => {
      const url = req.url();
      if (!url.startsWith("http://localhost") && !url.startsWith("about:")) {
        outboundRequests.push(url);
      }
    });
    await page.goto("/templates/tpl-001");
    // Wait for iframe to render
    await page.waitForTimeout(500);
    expect(outboundRequests).toHaveLength(0);
  });

  test("404 for unknown template", async ({ page }) => {
    const response = await page.goto("/templates/nonexistent-id");
    expect(response?.status()).toBe(404);
  });

  test("create template dialog opens", async ({ page }) => {
    await page.goto("/templates");
    await page.getByRole("button", { name: "New template" }).click();
    await expect(
      page.getByRole("dialog", { name: "Create template" }),
    ).toBeVisible();
  });

  test("template list page — a11y", async ({ page }) => {
    await page.goto("/templates");
    const results = await new AxeBuilder({ page }).analyze();
    expect(results.violations).toHaveLength(0);
  });

  test("template editor page — a11y", async ({ page }) => {
    await page.goto("/templates/tpl-001");
    const results = await new AxeBuilder({ page }).analyze();
    expect(results.violations).toHaveLength(0);
  });
});
