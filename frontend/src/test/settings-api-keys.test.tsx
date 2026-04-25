import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ApiKeysManager } from "@/app/(dashboard)/settings/api-keys/_components/api-keys-manager";

describe("ApiKeysManager", () => {
  it("clears the plaintext key when the modal closes", async () => {
    vi.stubGlobal("crypto", {
      ...crypto,
      randomUUID: () => "generated-key-id",
    });

    render(
      <ApiKeysManager
        initialKeys={[
          {
            id: "seed-key",
            name: "Import worker",
            prefix: "ak_live_seed01",
            last4: "A1b2",
            createdAt: "2026-04-18T08:25:00.000Z",
            lastUsedAt: null,
            revokedAt: null,
            status: "active",
          },
        ]}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Create key" }));
    const dialog = screen.getByRole("dialog");
    fireEvent.change(within(dialog).getByLabelText("Key name"), {
      target: { value: "Ops rotation" },
    });
    fireEvent.click(within(dialog).getByRole("button", { name: "Create key" }));

    const plaintextKey = await within(screen.getByRole("dialog")).findByText(
      /^ak_live_/i,
    );
    expect(plaintextKey).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Close and clear" }));
    fireEvent.click(screen.getByRole("button", { name: "Create key" }));

    await waitFor(() => {
      const reopenedDialog = screen.getByRole("dialog");

      expect(
        within(reopenedDialog).queryByText(plaintextKey.textContent ?? ""),
      ).not.toBeInTheDocument();
      expect(within(reopenedDialog).getByLabelText("Key name")).toHaveValue("");
    });
  });
});
