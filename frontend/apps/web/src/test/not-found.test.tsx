import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import NotFound from "@/app/not-found";

describe("NotFound", () => {
  it("renders recovery actions for missing routes", () => {
    render(<NotFound />);

    expect(
      screen.getByRole("heading", {
        name: "Page not found",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", {
        name: "Return to dashboard",
      }),
    ).toHaveAttribute("href", "/");
    expect(
      screen.getByRole("link", {
        name: "Open login placeholder",
      }),
    ).toHaveAttribute("href", "/login");
  });
});
