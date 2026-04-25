import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { MfaForm } from "@/app/(auth)/mfa/_components/mfa-form";
import { clientJson } from "@/lib/api/client";
import { ApiError } from "@/lib/api/errors";

vi.mock("@/lib/api/client", () => ({
  clientJson: vi.fn(),
}));

const challenge = {
  maskedEmail: "op*****@dispatch.internal",
  expiresAt: "2026-04-24T12:00:00.000Z",
  nextUrl: "/analytics",
} as const;

describe("MfaForm", () => {
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

  it("autosubmits a sanitized six-digit code", async () => {
    vi.mocked(clientJson).mockResolvedValueOnce({
      status: "authenticated",
      session: {
        id: "dev:operator@dispatch.internal",
        email: "operator@dispatch.internal",
        name: "Dispatch Operator",
        role: "admin",
      },
      source: "dev",
      challenge: null,
      nextUrl: "/analytics",
    });

    render(<MfaForm challenge={challenge} nextUrl="/analytics" />);

    fireEvent.change(screen.getByLabelText("Six-digit code"), {
      target: { value: "12 3a45-6" },
    });

    await waitFor(() => {
      expect(clientJson).toHaveBeenCalledWith("/api/session", {
        method: "PUT",
        body: {
          code: "123456",
          nextUrl: "/analytics",
        },
        redirectOnUnauthorized: false,
      });
      expect(locationAssign).toHaveBeenCalledWith("/analytics");
    });
  });

  it("shows a non-leaky retry message when the challenge is rate-limited", async () => {
    vi.mocked(clientJson).mockRejectedValueOnce(
      new ApiError("Verification unavailable - start again.", 429, {
        code: "rate_limited",
        method: "PUT",
        path: "/api/session",
      }),
    );

    render(<MfaForm challenge={challenge} nextUrl="/analytics" />);

    fireEvent.change(screen.getByLabelText("Six-digit code"), {
      target: { value: "111111" },
    });

    expect(
      await screen.findByText("Verification unavailable - start again."),
    ).toBeInTheDocument();
  });
});
