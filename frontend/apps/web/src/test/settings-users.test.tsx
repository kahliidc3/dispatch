import { fireEvent, render, screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { UsersManager } from "@/app/(dashboard)/settings/users/_components/users-manager";

describe("UsersManager", () => {
  it("creates a user and updates MFA state from the table actions", async () => {
    vi.stubGlobal("crypto", {
      ...crypto,
      randomUUID: () => "generated-user-id",
    });

    render(
      <UsersManager
        initialUsers={[
          {
            id: "seed-user",
            name: "Ops Admin",
            email: "ops-admin@dispatch.internal",
            role: "admin",
            status: "active",
            lastLoginAt: "2026-04-23T11:20:00.000Z",
            mfaState: "enrolled",
          },
        ]}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Create user" }));
    const dialog = screen.getByRole("dialog");
    fireEvent.change(within(dialog).getByLabelText("Full name"), {
      target: { value: "QA Operator" },
    });
    fireEvent.change(within(dialog).getByLabelText("Email"), {
      target: { value: "qa@dispatch.internal" },
    });
    fireEvent.click(within(dialog).getByRole("button", { name: "Create user" }));

    expect(await screen.findByText("QA Operator")).toBeInTheDocument();

    const resetButtons = screen.getAllByRole("button", { name: "Reset MFA" });
    fireEvent.click(resetButtons[0]);

    expect(await screen.findByText("reset required")).toBeInTheDocument();
  });
});
