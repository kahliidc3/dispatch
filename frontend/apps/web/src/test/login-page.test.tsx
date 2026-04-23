import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import LoginPage from "@/app/(auth)/login/page";

describe("LoginPage", () => {
  it("renders the auth placeholder fields", () => {
    render(<LoginPage />);

    expect(
      screen.getByRole("heading", {
        name: "Sign in",
      }),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("Email")).toHaveAttribute("type", "email");
    expect(screen.getByLabelText("Password")).toHaveAttribute(
      "type",
      "password",
    );
    expect(
      screen.getByRole("button", {
        name: "Continue",
      }),
    ).toBeInTheDocument();
  });
});
