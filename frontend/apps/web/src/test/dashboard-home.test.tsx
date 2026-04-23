import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import DashboardHomePage from "@/app/(dashboard)/page";

describe("DashboardHomePage", () => {
  it("renders the Sprint 00 placeholder shell", () => {
    render(<DashboardHomePage />);

    expect(
      screen.getByRole("heading", {
        name: "Dispatch",
      }),
    ).toBeInTheDocument();
    expect(screen.getByText("Docs-first scaffold")).toBeInTheDocument();
    expect(
      screen.getByRole("table", {
        name: "Sprint 00 route coverage",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", {
        name: "Campaigns",
      }),
    ).toHaveAttribute("href", "/campaigns");
  });
});
