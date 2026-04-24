import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { trackError } from "@/lib/telemetry";
import GlobalError from "@/app/global-error";

vi.mock("@/lib/telemetry", () => ({
  trackError: vi.fn().mockResolvedValue(undefined),
}));

describe("GlobalError", () => {
  it("renders the root error fallback, reports it, and retries", async () => {
    const reset = vi.fn();
    const error = new Error("scaffold failure");

    render(<GlobalError error={error} reset={reset} />);

    expect(
      screen.getByRole("heading", {
        name: "Application error",
      }),
    ).toBeInTheDocument();
    expect(screen.getByText("scaffold failure")).toBeInTheDocument();
    await waitFor(() => {
      expect(trackError).toHaveBeenCalledWith(error, {
        boundary: "global",
        digest: null,
      });
    });

    fireEvent.click(
      screen.getByRole("button", {
        name: "Retry",
      }),
    );

    expect(reset).toHaveBeenCalledTimes(1);
  });
});
