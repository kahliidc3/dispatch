import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { BreakerConsole } from "@/app/(dashboard)/ops/circuit-breakers/_components/breaker-console";
import { ResetDialog } from "@/app/(dashboard)/ops/circuit-breakers/_components/reset-dialog";
import { CircuitBreakerBadge } from "@/components/shared/circuit-breaker-badge";
import {
  getBreakerMatrix,
  getBreakerTimeline,
  getBreakerForEntity,
  getOpenBreakerCount,
} from "@/app/(dashboard)/ops/_lib/ops-queries";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

vi.mock("sonner", () => ({ toast: { success: vi.fn(), error: vi.fn() } }));

vi.mock("@/lib/api/client", () => ({
  clientJson: vi.fn().mockResolvedValue({}),
}));

// ─── getBreakerMatrix ─────────────────────────────────────────────────────────

describe("getBreakerMatrix", () => {
  it("returns 8 entries covering all 4 scopes", () => {
    const matrix = getBreakerMatrix();
    expect(matrix).toHaveLength(8);
    const scopes = new Set(matrix.map((e) => e.scope));
    expect(scopes.has("domain")).toBe(true);
    expect(scopes.has("ip_pool")).toBe(true);
    expect(scopes.has("sender_profile")).toBe(true);
    expect(scopes.has("account")).toBe(true);
  });

  it("dom-003 is open with high bounce rate", () => {
    const entry = getBreakerMatrix().find((e) => e.entityId === "dom-003");
    expect(entry?.state).toBe("open");
    expect(entry?.reason).toBe("high_bounce_rate");
    expect(entry?.bounceRatePct).toBeGreaterThan(1.5);
  });

  it("account is closed", () => {
    const entry = getBreakerMatrix().find((e) => e.scope === "account");
    expect(entry?.state).toBe("closed");
  });

  it("pool-002 has no auto-reset (manual only)", () => {
    const entry = getBreakerMatrix().find((e) => e.entityId === "pool-002");
    expect(entry?.autoResetAt).toBeNull();
  });
});

// ─── getBreakerTimeline ───────────────────────────────────────────────────────

describe("getBreakerTimeline", () => {
  it("returns timeline for cbr-dom-003", () => {
    const events = getBreakerTimeline("cbr-dom-003");
    expect(events.length).toBeGreaterThanOrEqual(2);
    expect(events[0]!.type).toBe("tripped");
  });

  it("first event has bounce rate", () => {
    const events = getBreakerTimeline("cbr-dom-003");
    expect(events[0]!.bounceRatePct).toBeGreaterThan(1.5);
  });

  it("reset event has actor and justification", () => {
    const events = getBreakerTimeline("cbr-dom-003");
    const reset = events.find((e) => e.type === "reset");
    expect(reset?.actor).toBeTruthy();
    expect(reset?.justification).toBeTruthy();
  });

  it("returns empty array for unknown breaker", () => {
    expect(getBreakerTimeline("unknown")).toHaveLength(0);
  });
});

// ─── getBreakerForEntity ──────────────────────────────────────────────────────

describe("getBreakerForEntity", () => {
  it("finds dom-003 domain breaker", () => {
    const b = getBreakerForEntity("domain", "dom-003");
    expect(b).not.toBeNull();
    expect(b?.state).toBe("open");
  });

  it("finds sp-002 sender profile breaker", () => {
    const b = getBreakerForEntity("sender_profile", "sp-002");
    expect(b?.state).toBe("open");
  });

  it("returns null for unknown entity", () => {
    expect(getBreakerForEntity("domain", "unknown")).toBeNull();
  });
});

// ─── getOpenBreakerCount ──────────────────────────────────────────────────────

describe("getOpenBreakerCount", () => {
  it("returns 3 (dom-003, pool-002, sp-002)", () => {
    expect(getOpenBreakerCount()).toBe(3);
  });
});

// ─── CircuitBreakerBadge ──────────────────────────────────────────────────────

describe("CircuitBreakerBadge", () => {
  it("renders open badge with danger link", () => {
    render(
      <CircuitBreakerBadge scope="domain" entityId="dom-003" state="open" />,
    );
    const link = screen.getByRole("link");
    expect(link).toHaveAttribute(
      "href",
      "/ops/circuit-breakers?scope=domain&entity=dom-003",
    );
    expect(screen.getByText("open")).toBeInTheDocument();
  });

  it("renders closed badge", () => {
    render(
      <CircuitBreakerBadge scope="domain" entityId="dom-001" state="closed" />,
    );
    expect(screen.getByText("closed")).toBeInTheDocument();
  });

  it("renders half_open badge", () => {
    render(
      <CircuitBreakerBadge scope="domain" entityId="dom-001" state="half_open" />,
    );
    expect(screen.getByText("half_open")).toBeInTheDocument();
  });
});

// ─── BreakerConsole ───────────────────────────────────────────────────────────

describe("BreakerConsole", () => {
  const entries = getBreakerMatrix();

  it("renders all four scope headings", () => {
    render(<BreakerConsole initialEntries={entries} />);
    expect(screen.getByText("Domain")).toBeInTheDocument();
    expect(screen.getByText("IP pool")).toBeInTheDocument();
    expect(screen.getByText("Sender profile")).toBeInTheDocument();
    expect(screen.getByText("Account")).toBeInTheDocument();
  });

  it("renders entity names", () => {
    render(<BreakerConsole initialEntries={entries} />);
    expect(screen.getByText("m49.dispatch.internal")).toBeInTheDocument();
    expect(screen.getByText("dedicated-pool-us-east-01")).toBeInTheDocument();
    expect(screen.getByText("Transactional alerts")).toBeInTheDocument();
  });

  it("shows open count status", () => {
    render(<BreakerConsole initialEntries={entries} />);
    expect(screen.getByRole("status")).toBeInTheDocument();
    expect(screen.getByRole("status").textContent).toMatch(/3 open/i);
  });

  it("renders Reset buttons for open entries only", () => {
    render(<BreakerConsole initialEntries={entries} />);
    const resetButtons = screen.getAllByRole("button", { name: /reset/i });
    expect(resetButtons).toHaveLength(3);
  });

  it("filter buttons are rendered", () => {
    render(<BreakerConsole initialEntries={entries} />);
    expect(screen.getByRole("button", { name: /open only/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /last 24h/i })).toBeInTheDocument();
  });

  it("'Open only' filter hides closed entries", () => {
    render(<BreakerConsole initialEntries={entries} />);
    fireEvent.click(screen.getByRole("button", { name: /open only/i }));
    expect(screen.queryByText("m47.dispatch.internal")).not.toBeInTheDocument();
    expect(screen.getByText("m49.dispatch.internal")).toBeInTheDocument();
  });

  it("'All' filter shows all entries", () => {
    render(<BreakerConsole initialEntries={entries} />);
    fireEvent.click(screen.getByRole("button", { name: /open only/i }));
    fireEvent.click(screen.getByRole("button", { name: /^all$/i }));
    expect(screen.getByText("m47.dispatch.internal")).toBeInTheDocument();
  });

  it("expand button toggles timeline", () => {
    render(<BreakerConsole initialEntries={entries} />);
    const expandButtons = screen
      .getAllByRole("button")
      .filter((b) => b.hasAttribute("aria-expanded"));
    fireEvent.click(expandButtons[0]!);
    expect(screen.getByText("Trip timeline")).toBeInTheDocument();
  });

  it("clicking Reset opens the reset dialog", () => {
    render(<BreakerConsole initialEntries={entries} />);
    const resetButton = screen.getAllByRole("button", { name: /^reset$/i })[0]!;
    fireEvent.click(resetButton);
    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(screen.getByText("Reset circuit breaker")).toBeInTheDocument();
  });
});

// ─── ResetDialog ──────────────────────────────────────────────────────────────

describe("ResetDialog", () => {
  const openEntry = getBreakerMatrix().find((e) => e.entityId === "dom-003")!;

  it("does not render when entry is null", () => {
    render(
      <ResetDialog entry={null} onClose={vi.fn()} onReset={vi.fn()} />,
    );
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("renders dialog when entry is provided", () => {
    render(
      <ResetDialog entry={openEntry} onClose={vi.fn()} onReset={vi.fn()} />,
    );
    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(screen.getByText("Reset circuit breaker")).toBeInTheDocument();
  });

  it("shows entity name and reason", () => {
    render(
      <ResetDialog entry={openEntry} onClose={vi.fn()} onReset={vi.fn()} />,
    );
    expect(screen.getByText(/m49\.dispatch\.internal/)).toBeInTheDocument();
    expect(screen.getByText("High bounce rate")).toBeInTheDocument();
  });

  it("submit is disabled when justification is too short", () => {
    render(
      <ResetDialog entry={openEntry} onClose={vi.fn()} onReset={vi.fn()} />,
    );
    fireEvent.change(screen.getByLabelText(/justification/i), {
      target: { value: "short" },
    });
    expect(screen.getByRole("button", { name: /reset breaker/i })).toBeDisabled();
  });

  it("submit is enabled with valid justification", () => {
    render(
      <ResetDialog entry={openEntry} onClose={vi.fn()} onReset={vi.fn()} />,
    );
    fireEvent.change(screen.getByLabelText(/justification/i), {
      target: { value: "Metrics are clean now, bounce rate dropped below threshold." },
    });
    expect(screen.getByRole("button", { name: /reset breaker/i })).not.toBeDisabled();
  });

  it("account scope shows extra warning and checkbox", () => {
    const accountEntry = getBreakerMatrix().find((e) => e.scope === "account")!;
    const openAccount = { ...accountEntry, state: "open" as const };
    render(
      <ResetDialog entry={openAccount} onClose={vi.fn()} onReset={vi.fn()} />,
    );
    expect(screen.getByRole("alert")).toBeInTheDocument();
    expect(
      screen.getByLabelText(/I understand this affects all sends/i),
    ).toBeInTheDocument();
  });

  it("account reset stays disabled without checkbox", () => {
    const openAccount = {
      ...getBreakerMatrix().find((e) => e.scope === "account")!,
      state: "open" as const,
    };
    render(
      <ResetDialog entry={openAccount} onClose={vi.fn()} onReset={vi.fn()} />,
    );
    fireEvent.change(screen.getByLabelText(/justification/i), {
      target: { value: "Account metrics verified clean and within thresholds." },
    });
    expect(screen.getByRole("button", { name: /reset breaker/i })).toBeDisabled();
  });

  it("account reset enables after checking box", () => {
    const openAccount = {
      ...getBreakerMatrix().find((e) => e.scope === "account")!,
      state: "open" as const,
    };
    render(
      <ResetDialog entry={openAccount} onClose={vi.fn()} onReset={vi.fn()} />,
    );
    fireEvent.change(screen.getByLabelText(/justification/i), {
      target: { value: "Account metrics verified clean and within thresholds." },
    });
    fireEvent.click(
      screen.getByLabelText(/I understand this affects all sends/i),
    );
    expect(screen.getByRole("button", { name: /reset breaker/i })).not.toBeDisabled();
  });
});
