import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { LoginForm } from "@/app/(auth)/login/_components/login-form";
import { clientJson } from "@/lib/api/client";

vi.mock("@/lib/api/client", () => ({
  clientJson: vi.fn(),
}));

describe("LoginForm", () => {
  const locationAssign = vi.fn();
  const originalLocation = window.location;

  beforeEach(() => {
    vi.mocked(clientJson).mockReset();
    Object.defineProperty(window, "location", {
      configurable: true,
      value: {
        ...originalLocation,
        assign: locationAssign,
      },
    });
    locationAssign.mockReset();
  });

  afterEach(() => {
    Object.defineProperty(window, "location", {
      configurable: true,
      value: originalLocation,
    });
  });

  it("renders auth fields and contextual reason copy", () => {
    render(<LoginForm nextUrl="/" reason="challenge-expired" />);

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
        name: "Continue to verification",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/verification step expired/i),
    ).toBeInTheDocument();
  });

  it("validates the form before submitting", async () => {
    render(<LoginForm nextUrl="/domains" reason={null} />);

    fireEvent.change(screen.getByLabelText("Email"), {
      target: { value: "invalid-email" },
    });
    fireEvent.change(screen.getByLabelText("Password"), {
      target: { value: "short" },
    });
    fireEvent.submit(
      screen
        .getByRole("button", {
          name: "Continue to verification",
        })
        .closest("form")!,
    );

    expect(
      await screen.findByText("Enter a valid work email."),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Enter the password assigned for this operator account."),
    ).toBeInTheDocument();
    expect(clientJson).not.toHaveBeenCalled();
  });

  it("redirects to MFA when the session route requires verification", async () => {
    vi.mocked(clientJson).mockResolvedValueOnce({
      status: "mfa_required",
      session: null,
      source: null,
      challenge: {
        maskedEmail: "op*****@dispatch.internal",
        expiresAt: "2026-04-24T12:00:00.000Z",
        nextUrl: "/settings/users",
      },
      nextUrl: "/settings/users",
    });

    render(<LoginForm nextUrl="/settings/users" reason={null} />);

    fireEvent.change(screen.getByLabelText("Password"), {
      target: { value: "dispatch-demo-password" },
    });
    fireEvent.submit(screen.getByRole("button", { name: "Continue to verification" }).closest("form")!);

    await waitFor(() => {
      expect(locationAssign).toHaveBeenCalledWith("/mfa?next=%2Fsettings%2Fusers");
    });
  });
});
