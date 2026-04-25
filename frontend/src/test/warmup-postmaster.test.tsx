import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { WarmupTab } from "@/app/(dashboard)/domains/[domainId]/_components/warmup-tab";
import { ReputationTab } from "@/app/(dashboard)/domains/[domainId]/_components/reputation-tab";
import { WarmingDomains } from "@/app/(dashboard)/analytics/_components/warming-domains";
import {
  getWarmupStatus,
  getPostmasterData,
  getWarmingDomains,
  STANDARD_CAPS,
  AGGRESSIVE_CAPS,
  capsForPreset,
} from "@/app/(dashboard)/domains/_lib/warmup-queries";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

vi.mock("sonner", () => ({ toast: { success: vi.fn(), error: vi.fn() } }));

vi.mock("@/lib/api/client", () => ({
  clientJson: vi.fn().mockResolvedValue({}),
}));

// ─── getWarmupStatus ──────────────────────────────────────────────────────────

describe("getWarmupStatus", () => {
  it("returns null for unknown domain", () => {
    expect(getWarmupStatus("unknown")).toBeNull();
  });

  it("dom-001 is day 0 (not started)", () => {
    const w = getWarmupStatus("dom-001")!;
    expect(w.currentDay).toBe(0);
    expect(w.todaySends).toBe(0);
  });

  it("dom-002 is in progress on day 23", () => {
    const w = getWarmupStatus("dom-002")!;
    expect(w.currentDay).toBe(23);
    expect(w.lifecycle).toBe("warming");
  });

  it("dom-002 has a scheduled graduation date", () => {
    const w = getWarmupStatus("dom-002")!;
    expect(w.scheduledGraduationAt).toBeTruthy();
  });

  it("dom-003 is overpacing (sends > cap)", () => {
    const w = getWarmupStatus("dom-003")!;
    expect(w.todaySends).toBeGreaterThan(w.todayCap);
  });

  it("schedule has correct total days for standard preset", () => {
    const w = getWarmupStatus("dom-002")!;
    expect(w.schedule.totalDays).toBe(STANDARD_CAPS.length);
    expect(w.schedule.days).toHaveLength(STANDARD_CAPS.length);
  });

  it("past days have actualSends, future days are null", () => {
    const w = getWarmupStatus("dom-002")!;
    const pastDays = w.schedule.days.slice(0, w.currentDay);
    const futureDays = w.schedule.days.slice(w.currentDay);
    expect(pastDays.every((d) => d.actualSends !== null)).toBe(true);
    expect(futureDays.every((d) => d.actualSends === null)).toBe(true);
  });
});

// ─── capsForPreset ────────────────────────────────────────────────────────────

describe("capsForPreset", () => {
  it("aggressive starts at 500", () => {
    expect(capsForPreset("aggressive")[0]).toBe(500);
  });

  it("standard has 30 entries", () => {
    expect(capsForPreset("standard")).toHaveLength(30);
  });

  it("conservative has 45 entries", () => {
    expect(capsForPreset("conservative")).toHaveLength(45);
  });

  it("aggressive first cap triggers 5x rule against dom-001 (todayCap=50)", () => {
    const aggressiveDay1 = AGGRESSIVE_CAPS[0]!;
    expect(aggressiveDay1).toBeGreaterThan(50 * 5);
  });
});

// ─── getPostmasterData ────────────────────────────────────────────────────────

describe("getPostmasterData", () => {
  it("dom-001 is not connected", () => {
    expect(getPostmasterData("dom-001").connected).toBe(false);
  });

  it("dom-002 is connected with 7 metrics", () => {
    const d = getPostmasterData("dom-002");
    expect(d.connected).toBe(true);
    expect(d.metrics).toHaveLength(7);
  });

  it("dom-002 metrics all have high reputation", () => {
    const d = getPostmasterData("dom-002");
    expect(d.metrics.every((m) => m.domainReputation === "high")).toBe(true);
  });

  it("dom-003 has medium or low reputation", () => {
    const d = getPostmasterData("dom-003");
    expect(
      d.metrics.every((m) => m.domainReputation === "medium" || m.domainReputation === "low"),
    ).toBe(true);
  });

  it("unknown domain returns disconnected", () => {
    const d = getPostmasterData("unknown");
    expect(d.connected).toBe(false);
    expect(d.metrics).toHaveLength(0);
  });
});

// ─── getWarmingDomains ────────────────────────────────────────────────────────

describe("getWarmingDomains", () => {
  it("returns 3 warming domains", () => {
    expect(getWarmingDomains()).toHaveLength(3);
  });

  it("includes dom-003 which is overpacing", () => {
    const dom3 = getWarmingDomains().find((d) => d.id === "dom-003");
    expect(dom3).toBeDefined();
    expect(dom3!.todaySends).toBeGreaterThan(dom3!.todayCap);
  });

  it("pctComplete for dom-002 is correct", () => {
    const dom2 = getWarmingDomains().find((d) => d.id === "dom-002");
    expect(dom2!.pctComplete).toBe(Math.round((23 / 30) * 100));
  });
});

// ─── WarmupTab ────────────────────────────────────────────────────────────────

describe("WarmupTab", () => {
  const dom001 = getWarmupStatus("dom-001")!;
  const dom002 = getWarmupStatus("dom-002")!;
  const dom003 = getWarmupStatus("dom-003")!;

  it("renders progress bar", () => {
    render(<WarmupTab domainId="dom-002" warmup={dom002} />);
    expect(screen.getByRole("progressbar")).toBeInTheDocument();
  });

  it("shows 'Not yet started' for day-0 domain", () => {
    render(<WarmupTab domainId="dom-001" warmup={dom001} />);
    expect(screen.getByText(/not yet started/i)).toBeInTheDocument();
  });

  it("shows current day/total for dom-002", () => {
    render(<WarmupTab domainId="dom-002" warmup={dom002} />);
    expect(screen.getByText(/day 23 of 30/i)).toBeInTheDocument();
  });

  it("shows scheduled graduation for dom-002", () => {
    render(<WarmupTab domainId="dom-002" warmup={dom002} />);
    expect(screen.getByText(/scheduled graduation/i)).toBeInTheDocument();
  });

  it("shows overpacing banner for dom-003", () => {
    render(<WarmupTab domainId="dom-003" warmup={dom003} />);
    expect(screen.getByRole("alert")).toBeInTheDocument();
    expect(screen.getByText(/volume exceeding cap/i)).toBeInTheDocument();
  });

  it("no overpacing banner for dom-002", () => {
    render(<WarmupTab domainId="dom-002" warmup={dom002} />);
    expect(screen.queryByText(/volume exceeding cap/i)).not.toBeInTheDocument();
  });

  it("shows upcoming schedule table", () => {
    render(<WarmupTab domainId="dom-002" warmup={dom002} />);
    expect(screen.getByText(/upcoming schedule/i)).toBeInTheDocument();
  });

  it("shows Extend by 7 days button", () => {
    render(<WarmupTab domainId="dom-002" warmup={dom002} />);
    expect(
      screen.getByRole("button", { name: /extend by 7 days/i }),
    ).toBeInTheDocument();
  });

  it("Edit schedule button opens editor", () => {
    render(<WarmupTab domainId="dom-002" warmup={dom002} />);
    fireEvent.click(screen.getByRole("button", { name: /edit schedule/i }));
    expect(screen.getByText(/choose a preset schedule/i)).toBeInTheDocument();
  });

  it("preset buttons rendered in editor", () => {
    render(<WarmupTab domainId="dom-002" warmup={dom002} />);
    fireEvent.click(screen.getByRole("button", { name: /edit schedule/i }));
    expect(screen.getByRole("button", { name: /conservative/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /standard/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /aggressive/i })).toBeInTheDocument();
  });

  it("selecting aggressive on dom-001 shows 5x warning", () => {
    render(<WarmupTab domainId="dom-001" warmup={dom001} />);
    fireEvent.click(screen.getByRole("button", { name: /edit schedule/i }));
    fireEvent.click(screen.getByRole("button", { name: /aggressive/i }));
    expect(screen.getByRole("alert")).toBeInTheDocument();
    expect(screen.getByText(/aggressive schedule warning/i)).toBeInTheDocument();
  });

  it("save disabled until 5x confirm checked", () => {
    render(<WarmupTab domainId="dom-001" warmup={dom001} />);
    fireEvent.click(screen.getByRole("button", { name: /edit schedule/i }));
    fireEvent.click(screen.getByRole("button", { name: /aggressive/i }));
    expect(screen.getByRole("button", { name: /save schedule/i })).toBeDisabled();
  });

  it("save enabled after checking confirm", () => {
    render(<WarmupTab domainId="dom-001" warmup={dom001} />);
    fireEvent.click(screen.getByRole("button", { name: /edit schedule/i }));
    fireEvent.click(screen.getByRole("button", { name: /aggressive/i }));
    fireEvent.click(
      screen.getByRole("checkbox", { name: /understand the risk/i }),
    );
    expect(screen.getByRole("button", { name: /save schedule/i })).not.toBeDisabled();
  });

  it("cancel closes editor", () => {
    render(<WarmupTab domainId="dom-002" warmup={dom002} />);
    fireEvent.click(screen.getByRole("button", { name: /edit schedule/i }));
    fireEvent.click(screen.getByRole("button", { name: /cancel/i }));
    expect(screen.queryByText(/choose a preset schedule/i)).not.toBeInTheDocument();
  });
});

// ─── ReputationTab ────────────────────────────────────────────────────────────

describe("ReputationTab", () => {
  const disconnected = getPostmasterData("dom-001");
  const connected = getPostmasterData("dom-002");
  const dom003Data = getPostmasterData("dom-003");

  it("shows connect CTA when not connected", () => {
    render(<ReputationTab domainId="dom-001" data={disconnected} />);
    expect(screen.getByText(/google postmaster not connected/i)).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /connect postmaster/i }),
    ).toBeInTheDocument();
  });

  it("shows 'As of' timestamp when connected", () => {
    render(<ReputationTab domainId="dom-002" data={connected} />);
    expect(screen.getByText(/as of/i)).toBeInTheDocument();
  });

  it("shows 4 metric cards when connected", () => {
    render(<ReputationTab domainId="dom-002" data={connected} />);
    expect(screen.getAllByText(/spam rate/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/domain reputation/i)).toBeInTheDocument();
    expect(screen.getAllByText(/spf pass/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/dkim pass/i).length).toBeGreaterThan(0);
  });

  it("shows 7-day metrics table", () => {
    render(<ReputationTab domainId="dom-002" data={connected} />);
    expect(screen.getByText(/last 7 days/i)).toBeInTheDocument();
    const rows = screen.getAllByText(/high/);
    expect(rows.length).toBeGreaterThanOrEqual(1);
  });

  it("shows medium/low reputation for dom-003", () => {
    render(<ReputationTab domainId="dom-003" data={dom003Data} />);
    expect(screen.getAllByText(/medium|low/i).length).toBeGreaterThan(0);
  });

  it("shows Open Postmaster external link", () => {
    render(<ReputationTab domainId="dom-002" data={connected} />);
    expect(
      screen.getByRole("link", { name: /open postmaster/i }),
    ).toBeInTheDocument();
  });
});

// ─── WarmingDomains widget ────────────────────────────────────────────────────

describe("WarmingDomains", () => {
  const domains = getWarmingDomains();

  it("renders all 3 warming domains", () => {
    render(<WarmingDomains domains={domains} />);
    expect(screen.getByText("m47.dispatch.internal")).toBeInTheDocument();
    expect(screen.getByText("m48.dispatch.internal")).toBeInTheDocument();
    expect(screen.getByText("m49.dispatch.internal")).toBeInTheDocument();
  });

  it("renders mini progress bars", () => {
    render(<WarmingDomains domains={domains} />);
    expect(screen.getAllByRole("progressbar").length).toBe(3);
  });

  it("shows empty state when no warming domains", () => {
    render(<WarmingDomains domains={[]} />);
    expect(
      screen.getByText(/no domains currently in warmup/i),
    ).toBeInTheDocument();
  });

  it("domain name links to warmup tab", () => {
    render(<WarmingDomains domains={domains} />);
    const link = screen.getByRole("link", { name: "m48.dispatch.internal" });
    expect(link).toHaveAttribute("href", "/domains/dom-002?tab=warmup");
  });
});
