import { fireEvent, render, screen } from "@testing-library/react";
import type { ReactElement, ReactNode } from "react";
import { isValidElement } from "react";
import { describe, expect, it, vi } from "vitest";
import GlobalError from "@/app/global-error";

describe("GlobalError", () => {
  it("renders the root error fallback and retries", () => {
    const reset = vi.fn();
    const tree = GlobalError({
      error: new Error("scaffold failure"),
      reset,
    });

    expect(isValidElement(tree)).toBe(true);
    if (!isValidElement(tree)) {
      return;
    }

    const html = tree as ReactElement<{ children: ReactNode }>;
    const body = html.props.children;
    expect(isValidElement(body)).toBe(true);
    if (!isValidElement(body)) {
      return;
    }

    const bodyElement = body as ReactElement<{ children: ReactNode }>;

    render(bodyElement.props.children);

    expect(
      screen.getByRole("heading", {
        name: "Application error",
      }),
    ).toBeInTheDocument();
    expect(screen.getByText("scaffold failure")).toBeInTheDocument();

    fireEvent.click(
      screen.getByRole("button", {
        name: "Retry",
      }),
    );

    expect(reset).toHaveBeenCalledTimes(1);
  });
});
