import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import DashboardHomePage from "@/app/(dashboard)/page";

describe("DashboardHomePage", () => {
  it("renders the Sprint 01 shell summary", () => {
    render(<DashboardHomePage />);

    expect(
      screen.getByRole("heading", {
        name: "Dispatch",
      }),
    ).toBeInTheDocument();
    expect(screen.getByText("Core shell foundation")).toBeInTheDocument();
    expect(
      screen.getByRole("table", {
        name: "Sprint 01 route coverage",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", {
        name: "Campaigns",
      }),
    ).toHaveAttribute("href", "/campaigns");
  });
});
