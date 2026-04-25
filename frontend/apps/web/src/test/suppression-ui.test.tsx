import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { SuppressionManager } from "@/app/(dashboard)/suppression/_components/suppression-manager";
import { mockSuppressionList, mockSyncStatus } from "@/app/(dashboard)/suppression/_lib/suppression-queries";
import {
  SUPPRESSION_REASON_LABELS,
  SUPPRESSION_SOURCE_LABELS,
  SUPPRESSION_REASON_VARIANTS,
} from "@/types/suppression";
import { maskEmailAddress } from "@/lib/formatters";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), refresh: vi.fn() }),
}));

vi.mock("sonner", () => ({ toast: { success: vi.fn(), error: vi.fn() } }));

vi.mock("@/lib/api/client", () => ({
  clientJson: vi.fn(),
}));

const defaultProps = {
  initialEntries: mockSuppressionList,
  syncStatus: mockSyncStatus,
  isAdmin: false,
};

// ─── SUPPRESSION_REASON_LABELS ────────────────────────────────────────────────

describe("SUPPRESSION_REASON_LABELS", () => {
  it("has label for every reason", () => {
    expect(SUPPRESSION_REASON_LABELS.hard_bounce).toBe("Hard bounce");
    expect(SUPPRESSION_REASON_LABELS.spam_complaint).toBe("Spam complaint");
    expect(SUPPRESSION_REASON_LABELS.unsubscribe).toBe("Unsubscribe");
    expect(SUPPRESSION_REASON_LABELS.soft_bounce).toBe("Soft bounce");
    expect(SUPPRESSION_REASON_LABELS.manual).toBe("Manual");
  });
});

describe("SUPPRESSION_SOURCE_LABELS", () => {
  it("has label for every source", () => {
    expect(SUPPRESSION_SOURCE_LABELS.ses_event).toBe("SES event");
    expect(SUPPRESSION_SOURCE_LABELS.one_click).toBe("One-click");
    expect(SUPPRESSION_SOURCE_LABELS.csv_import).toBe("CSV import");
    expect(SUPPRESSION_SOURCE_LABELS.api).toBe("API");
    expect(SUPPRESSION_SOURCE_LABELS.manual).toBe("Manual");
  });
});

describe("SUPPRESSION_REASON_VARIANTS", () => {
  it("hard_bounce and spam_complaint are danger", () => {
    expect(SUPPRESSION_REASON_VARIANTS.hard_bounce).toBe("danger");
    expect(SUPPRESSION_REASON_VARIANTS.spam_complaint).toBe("danger");
  });

  it("soft_bounce and unsubscribe are warning", () => {
    expect(SUPPRESSION_REASON_VARIANTS.soft_bounce).toBe("warning");
    expect(SUPPRESSION_REASON_VARIANTS.unsubscribe).toBe("warning");
  });

  it("manual is muted", () => {
    expect(SUPPRESSION_REASON_VARIANTS.manual).toBe("muted");
  });
});

// ─── SuppressionManager ───────────────────────────────────────────────────────

describe("SuppressionManager", () => {
  it("renders suppression list table", () => {
    render(<SuppressionManager {...defaultProps} />);
    expect(
      screen.getByRole("table", { name: "Suppression list" }),
    ).toBeInTheDocument();
  });

  it("shows masked email addresses by default", () => {
    const entry = mockSuppressionList[0]!;
    render(<SuppressionManager {...defaultProps} />);
    const masked = maskEmailAddress(entry.email);
    expect(screen.getAllByText(masked).length).toBeGreaterThan(0);
  });

  it("does not show raw emails", () => {
    render(<SuppressionManager {...defaultProps} />);
    const entry = mockSuppressionList[0]!;
    // Raw email should not appear anywhere (only masked form is rendered)
    expect(screen.queryAllByText(entry.email)).toHaveLength(0);
  });

  it("shows reason badges", () => {
    render(<SuppressionManager {...defaultProps} />);
    expect(screen.getAllByText("Hard bounce").length).toBeGreaterThan(0);
  });

  it("shows SES sync panel", () => {
    render(<SuppressionManager {...defaultProps} />);
    expect(screen.getByText("SES suppression sync")).toBeInTheDocument();
  });

  it("shows In sync badge when driftCount is 0", () => {
    render(
      <SuppressionManager
        {...defaultProps}
        syncStatus={{ lastSyncAt: "2026-04-24T07:00:00Z", driftCount: 0 }}
      />,
    );
    expect(screen.getByText("In sync")).toBeInTheDocument();
  });

  it("shows drift badge when driftCount > 0", () => {
    render(
      <SuppressionManager
        {...defaultProps}
        syncStatus={{ lastSyncAt: "2026-04-24T07:00:00Z", driftCount: 2 }}
      />,
    );
    expect(screen.getByText("2 drifts")).toBeInTheDocument();
  });

  it("shows entry count", () => {
    render(<SuppressionManager {...defaultProps} />);
    expect(
      screen.getByText(`${mockSuppressionList.length} entries`),
    ).toBeInTheDocument();
  });

  it("shows Add entry button", () => {
    render(<SuppressionManager {...defaultProps} />);
    expect(
      screen.getByRole("button", { name: "Add entry" }),
    ).toBeInTheDocument();
  });

  it("shows Bulk add button", () => {
    render(<SuppressionManager {...defaultProps} />);
    expect(
      screen.getByRole("button", { name: "Bulk add" }),
    ).toBeInTheDocument();
  });

  it("shows Export CSV button", () => {
    render(<SuppressionManager {...defaultProps} />);
    expect(
      screen.getByRole("button", { name: "Export CSV" }),
    ).toBeInTheDocument();
  });

  it("does not show Remove button for non-admins", () => {
    render(<SuppressionManager {...defaultProps} isAdmin={false} />);
    expect(
      screen.queryByRole("button", { name: /remove/i }),
    ).not.toBeInTheDocument();
  });

  it("shows Remove button for admins", () => {
    render(<SuppressionManager {...defaultProps} isAdmin={true} />);
    expect(
      screen.getAllByRole("button", { name: /remove/i }).length,
    ).toBeGreaterThan(0);
  });

  it("does not show Reveal button for non-admins", () => {
    render(<SuppressionManager {...defaultProps} isAdmin={false} />);
    expect(screen.queryByText("Reveal")).not.toBeInTheDocument();
  });

  it("shows Reveal button for admins", () => {
    render(<SuppressionManager {...defaultProps} isAdmin={true} />);
    expect(screen.getAllByText("Reveal").length).toBeGreaterThan(0);
  });

  it("opens single-add dialog on click", () => {
    render(<SuppressionManager {...defaultProps} />);
    fireEvent.click(screen.getByRole("button", { name: "Add entry" }));
    expect(
      screen.getByRole("dialog", { name: "Add suppression entry" }),
    ).toBeInTheDocument();
  });

  it("opens bulk-add dialog on click", () => {
    render(<SuppressionManager {...defaultProps} />);
    fireEvent.click(screen.getByRole("button", { name: "Bulk add" }));
    expect(
      screen.getByRole("dialog", { name: "Bulk add suppression entries" }),
    ).toBeInTheDocument();
  });

  it("filtering by reason narrows results", () => {
    render(<SuppressionManager {...defaultProps} />);
    const reasonFilter = screen.getByRole("combobox", { name: "Filter by reason" });
    fireEvent.change(reasonFilter, { target: { value: "hard_bounce" } });
    const hardBounceCount = mockSuppressionList.filter(
      (e) => e.reason === "hard_bounce",
    ).length;
    expect(screen.getByText(`${hardBounceCount} entries`)).toBeInTheDocument();
  });

  it("search by email narrows results", () => {
    render(<SuppressionManager {...defaultProps} />);
    const searchInput = screen.getByRole("searchbox", { name: "Search by email" });
    fireEvent.change(searchInput, { target: { value: "acme.com" } });
    const acmeCount = mockSuppressionList.filter((e) =>
      e.email.includes("acme.com"),
    ).length;
    expect(screen.getByText(`${acmeCount} entr${acmeCount !== 1 ? "ies" : "y"}`)).toBeInTheDocument();
  });

  it("add dialog requires email before enabling submit", () => {
    render(<SuppressionManager {...defaultProps} />);
    fireEvent.click(screen.getByRole("button", { name: "Add entry" }));
    expect(
      screen.getByRole("button", { name: "Add" }),
    ).toBeDisabled();
  });

  it("bulk add parses email count from textarea", () => {
    render(<SuppressionManager {...defaultProps} />);
    fireEvent.click(screen.getByRole("button", { name: "Bulk add" }));
    fireEvent.change(screen.getByLabelText("Email addresses"), {
      target: { value: "a@example.com\nb@example.com\nc@example.com" },
    });
    expect(screen.getByText("3 valid addresses parsed")).toBeInTheDocument();
  });

  it("bulk add deduplicates addresses", () => {
    render(<SuppressionManager {...defaultProps} />);
    fireEvent.click(screen.getByRole("button", { name: "Bulk add" }));
    fireEvent.change(screen.getByLabelText("Email addresses"), {
      target: { value: "a@example.com\na@example.com\nb@example.com" },
    });
    expect(screen.getByText("2 valid addresses parsed")).toBeInTheDocument();
  });

  it("remove dialog requires justification before enabling submit (admin)", () => {
    render(<SuppressionManager {...defaultProps} isAdmin={true} />);
    const removeBtns = screen.getAllByRole("button", { name: /remove/i });
    fireEvent.click(removeBtns[0]!);
    expect(
      screen.getByRole("button", { name: "Remove" }),
    ).toBeDisabled();
  });

  it("remove dialog submit enabled after typing justification", () => {
    render(<SuppressionManager {...defaultProps} isAdmin={true} />);
    const removeBtns = screen.getAllByRole("button", { name: /remove/i });
    fireEvent.click(removeBtns[0]!);
    fireEvent.change(screen.getByLabelText(/justification/i), {
      target: { value: "User requested removal" },
    });
    expect(
      screen.getByRole("button", { name: "Remove" }),
    ).not.toBeDisabled();
  });

  it("pagination shows when entries exceed page size", () => {
    // mockSuppressionList has 25 entries, PAGE_SIZE is 20
    render(<SuppressionManager {...defaultProps} />);
    expect(screen.getByRole("button", { name: "Next" })).toBeInTheDocument();
  });

  it("previous button is disabled on first page", () => {
    render(<SuppressionManager {...defaultProps} />);
    expect(
      screen.getByRole("button", { name: "Previous" }),
    ).toBeDisabled();
  });
});

// ─── maskEmailAddress ─────────────────────────────────────────────────────────

describe("maskEmailAddress", () => {
  it("masks middle of local part", () => {
    expect(maskEmailAddress("alice@example.com")).toBe("al***@example.com");
  });

  it("returns input unchanged when no @ symbol", () => {
    expect(maskEmailAddress("notanemail")).toBe("notanemail");
  });
});
