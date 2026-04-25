import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { ThroughputTab } from "@/app/(dashboard)/domains/[domainId]/_components/throughput-tab";
import { QueuesViewer } from "@/app/(dashboard)/ops/queues/_components/queues-viewer";
import {
  getThrottleStatus,
  getDenialEvents,
} from "@/app/(dashboard)/domains/_lib/domains-queries";
import {
  getQueueSnapshot,
  QUEUE_DEPTH_WARN_THRESHOLD,
} from "@/app/(dashboard)/ops/_lib/ops-queries";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

vi.mock("sonner", () => ({ toast: { success: vi.fn(), error: vi.fn() } }));

vi.mock("@/lib/api/client", () => ({
  clientJson: vi.fn().mockResolvedValue({}),
}));

// ─── getThrottleStatus ────────────────────────────────────────────────────────

describe("getThrottleStatus", () => {
  it("returns throttle data for dom-002", () => {
    const t = getThrottleStatus("dom-002");
    expect(t.domainId).toBe("dom-002");
    expect(t.rateLimit).toBe(300);
    expect(t.tokensAvailable).toBe(81);
    expect(t.denialsPerMinute).toBe(3.2);
  });

  it("returns throttle data for dom-003", () => {
    const t = getThrottleStatus("dom-003");
    expect(t.tokensAvailable).toBe(0);
    expect(t.denialsPerMinute).toBe(14.7);
  });

  it("returns default 150 limit for unknown domain", () => {
    const t = getThrottleStatus("unknown");
    expect(t.rateLimit).toBe(150);
    expect(t.tokensAvailable).toBe(150);
  });
});

// ─── getDenialEvents ──────────────────────────────────────────────────────────

describe("getDenialEvents", () => {
  it("returns denial events for dom-003", () => {
    const events = getDenialEvents("dom-003");
    expect(events.length).toBeGreaterThanOrEqual(3);
  });

  it("each event has required fields", () => {
    const events = getDenialEvents("dom-002");
    for (const ev of events) {
      expect(ev.id).toBeTruthy();
      expect(ev.occurredAt).toBeTruthy();
      expect(ev.reason).toBeTruthy();
      expect(ev.recipientCount).toBeGreaterThan(0);
    }
  });

  it("returns empty array for clean domain", () => {
    expect(getDenialEvents("dom-001")).toHaveLength(0);
  });
});

// ─── getQueueSnapshot ─────────────────────────────────────────────────────────

describe("getQueueSnapshot", () => {
  it("returns 3 rows", () => {
    expect(getQueueSnapshot()).toHaveLength(3);
  });

  it("each row has required fields", () => {
    for (const row of getQueueSnapshot()) {
      expect(row.domainId).toBeTruthy();
      expect(row.domainName).toBeTruthy();
      expect(row.queueName.startsWith("send.")).toBe(true);
      expect(row.workerCount).toBeGreaterThan(0);
    }
  });

  it("dom-003 queue depth exceeds warn threshold", () => {
    const rows = getQueueSnapshot();
    const row = rows.find((r) => r.domainId === "dom-003");
    expect(row?.queueDepth).toBeGreaterThan(QUEUE_DEPTH_WARN_THRESHOLD);
  });

  it("dom-001 queue is empty", () => {
    const rows = getQueueSnapshot();
    const row = rows.find((r) => r.domainId === "dom-001");
    expect(row?.queueDepth).toBe(0);
  });
});

// ─── ThroughputTab ────────────────────────────────────────────────────────────

describe("ThroughputTab", () => {
  const throttle = getThrottleStatus("dom-002");
  const denialEvents = getDenialEvents("dom-002");

  it("renders token bucket stats", () => {
    render(
      <ThroughputTab
        domainId="dom-002"
        throttle={throttle}
        denialEvents={denialEvents}
        isAdmin={true}
      />,
    );
    expect(screen.getByText("Rate limit")).toBeInTheDocument();
    expect(screen.getByText("Tokens available")).toBeInTheDocument();
    expect(screen.getByText("Refill rate")).toBeInTheDocument();
    expect(screen.getByText("Denials / min")).toBeInTheDocument();
  });

  it("renders rate limit value", () => {
    render(
      <ThroughputTab
        domainId="dom-002"
        throttle={throttle}
        denialEvents={denialEvents}
        isAdmin={true}
      />,
    );
    expect(screen.getByText("300")).toBeInTheDocument();
  });

  it("renders denial events table", () => {
    render(
      <ThroughputTab
        domainId="dom-002"
        throttle={throttle}
        denialEvents={denialEvents}
        isAdmin={true}
      />,
    );
    expect(screen.getByText("Recent denial events")).toBeInTheDocument();
    expect(screen.getAllByText(/token bucket empty/i).length).toBeGreaterThan(0);
  });

  it("shows edit form for admin", () => {
    render(
      <ThroughputTab
        domainId="dom-002"
        throttle={throttle}
        denialEvents={denialEvents}
        isAdmin={true}
      />,
    );
    expect(screen.getByLabelText("Sends per hour")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /save/i })).toBeInTheDocument();
  });

  it("hides edit form for non-admin", () => {
    render(
      <ThroughputTab
        domainId="dom-002"
        throttle={throttle}
        denialEvents={denialEvents}
        isAdmin={false}
      />,
    );
    expect(screen.queryByLabelText("Sends per hour")).not.toBeInTheDocument();
  });

  it("shows confirm prompt when reducing by > 50%", () => {
    render(
      <ThroughputTab
        domainId="dom-002"
        throttle={throttle}
        denialEvents={denialEvents}
        isAdmin={true}
      />,
    );
    const input = screen.getByLabelText("Sends per hour");
    fireEvent.change(input, { target: { value: "100" } });
    fireEvent.click(screen.getByRole("button", { name: /save/i }));
    expect(screen.getByRole("alert")).toBeInTheDocument();
    expect(screen.getByText(/more than 50%/i)).toBeInTheDocument();
  });

  it("save button changes to Confirm on drastic reduction", () => {
    render(
      <ThroughputTab
        domainId="dom-002"
        throttle={throttle}
        denialEvents={denialEvents}
        isAdmin={true}
      />,
    );
    const input = screen.getByLabelText("Sends per hour");
    fireEvent.change(input, { target: { value: "50" } });
    fireEvent.click(screen.getByRole("button", { name: /save/i }));
    expect(screen.getByRole("button", { name: /confirm/i })).toBeInTheDocument();
  });

  it("does not show confirm for moderate reduction", () => {
    render(
      <ThroughputTab
        domainId="dom-002"
        throttle={throttle}
        denialEvents={denialEvents}
        isAdmin={true}
      />,
    );
    const input = screen.getByLabelText("Sends per hour");
    fireEvent.change(input, { target: { value: "200" } });
    fireEvent.click(screen.getByRole("button", { name: /save/i }));
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("shows no events message for clean domain", () => {
    const clean = getThrottleStatus("dom-001");
    render(
      <ThroughputTab
        domainId="dom-001"
        throttle={clean}
        denialEvents={[]}
        isAdmin={true}
      />,
    );
    expect(screen.getByText(/no denial events/i)).toBeInTheDocument();
  });
});

// ─── QueuesViewer ─────────────────────────────────────────────────────────────

describe("QueuesViewer", () => {
  const rows = getQueueSnapshot();

  it("renders all domain rows", () => {
    render(<QueuesViewer initialRows={rows} />);
    expect(screen.getByText("m47.dispatch.internal")).toBeInTheDocument();
    expect(screen.getByText("m48.dispatch.internal")).toBeInTheDocument();
    expect(screen.getByText("m49.dispatch.internal")).toBeInTheDocument();
  });

  it("renders queue names", () => {
    render(<QueuesViewer initialRows={rows} />);
    expect(screen.getByText("send.m49.dispatch.internal")).toBeInTheDocument();
  });

  it("shows warning status for over-threshold queues", () => {
    render(<QueuesViewer initialRows={rows} />);
    expect(screen.getByRole("status")).toBeInTheDocument();
    expect(screen.getByRole("status").textContent).toMatch(/over threshold/i);
  });

  it("no warning status when all queues are healthy", () => {
    const healthy = rows.map((r) => ({ ...r, queueDepth: 0 }));
    render(<QueuesViewer initialRows={healthy} />);
    expect(screen.queryByRole("status")).not.toBeInTheDocument();
  });

  it("search filters rows", () => {
    render(<QueuesViewer initialRows={rows} />);
    fireEvent.change(screen.getByRole("searchbox", { name: /search domain/i }), {
      target: { value: "m47" },
    });
    expect(screen.getByText("m47.dispatch.internal")).toBeInTheDocument();
    expect(screen.queryByText("m48.dispatch.internal")).not.toBeInTheDocument();
  });

  it("shows empty message when search has no match", () => {
    render(<QueuesViewer initialRows={rows} />);
    fireEvent.change(screen.getByRole("searchbox", { name: /search domain/i }), {
      target: { value: "nonexistent" },
    });
    expect(screen.getByText(/no queues match/i)).toBeInTheDocument();
  });

  it("domain name links to throughput tab", () => {
    render(<QueuesViewer initialRows={rows} />);
    const link = screen.getByRole("link", { name: /m49\.dispatch\.internal/ });
    expect(link).toHaveAttribute("href", "/domains/dom-003?tab=throughput");
  });

  it("renders column sort buttons", () => {
    render(<QueuesViewer initialRows={rows} />);
    expect(screen.getByRole("button", { name: /depth/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /oldest age/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /denials\/min/i })).toBeInTheDocument();
  });
});
