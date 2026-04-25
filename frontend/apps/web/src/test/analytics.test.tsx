import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { KpiCards } from "@/app/(dashboard)/analytics/_components/kpi-cards";
import { FreshnessBanner } from "@/app/(dashboard)/analytics/_components/freshness-banner";
import { TopCampaigns } from "@/app/(dashboard)/analytics/_components/top-campaigns";
import { TopFailingDomains } from "@/app/(dashboard)/analytics/_components/top-failing-domains";
import {
  getAnalyticsMeta,
  getOverviewKpis,
  getTopCampaigns,
  getDomainReputationData,
  getEngagementTimeSeries,
  getOpenRateHeatmap,
  HEATMAP_DAY_LABELS,
  HEATMAP_HOUR_LABELS,
} from "@/app/(dashboard)/analytics/_lib/analytics-queries";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

// ─── analytics-queries ────────────────────────────────────────────────────────

describe("getAnalyticsMeta", () => {
  it("returns lastUpdatedAt and isStale", () => {
    const meta = getAnalyticsMeta();
    expect(meta.lastUpdatedAt).toBeDefined();
    expect(typeof meta.isStale).toBe("boolean");
  });
});

describe("getOverviewKpis", () => {
  it("returns 6 KPI entries", () => {
    expect(getOverviewKpis()).toHaveLength(6);
  });

  it("each KPI has label, value, trendValue", () => {
    for (const kpi of getOverviewKpis()) {
      expect(kpi.label).toBeTruthy();
      expect(kpi.value).toBeTruthy();
      expect(kpi.trendValue).toBeTruthy();
    }
  });

  it("includes sends today KPI", () => {
    const kpis = getOverviewKpis();
    expect(kpis.some((k) => k.label === "Sends today")).toBe(true);
  });
});

describe("getTopCampaigns", () => {
  it("returns at least 3 rows", () => {
    expect(getTopCampaigns().length).toBeGreaterThanOrEqual(3);
  });

  it("each row has sparkline with 7 points", () => {
    for (const row of getTopCampaigns()) {
      expect(row.sparkline).toHaveLength(7);
    }
  });
});

describe("getDomainReputationData", () => {
  it("returns domains with riskLevel", () => {
    const domains = getDomainReputationData();
    expect(domains.length).toBeGreaterThan(0);
    for (const d of domains) {
      expect(["ok", "warn", "critical"]).toContain(d.riskLevel);
    }
  });

  it("domain with high bounce rate is critical", () => {
    const domains = getDomainReputationData();
    const bad = domains.find((d) => d.bounceRate >= 1.5);
    expect(bad?.riskLevel).toBe("critical");
  });

  it("domain with zero rates is ok", () => {
    const domains = getDomainReputationData();
    const clean = domains.find(
      (d) => d.bounceRate === 0 && d.complaintRate === 0,
    );
    expect(clean?.riskLevel).toBe("ok");
  });
});

describe("getEngagementTimeSeries", () => {
  it("returns 14 data points", () => {
    expect(getEngagementTimeSeries()).toHaveLength(14);
  });

  it("each point has sent, delivered, bounced", () => {
    for (const p of getEngagementTimeSeries()) {
      expect(p.sent).toBeGreaterThan(0);
      expect(p.delivered).toBeGreaterThan(0);
      expect(p.bounced).toBeGreaterThanOrEqual(0);
    }
  });

  it("delivered <= sent for all points", () => {
    for (const p of getEngagementTimeSeries()) {
      expect(p.delivered).toBeLessThanOrEqual(p.sent);
    }
  });
});

describe("getOpenRateHeatmap", () => {
  it("returns 7 rows", () => {
    expect(getOpenRateHeatmap()).toHaveLength(7);
  });

  it("each row has 12 columns", () => {
    for (const row of getOpenRateHeatmap()) {
      expect(row).toHaveLength(12);
    }
  });

  it("HEATMAP_DAY_LABELS has 7 entries", () => {
    expect(HEATMAP_DAY_LABELS).toHaveLength(7);
  });

  it("HEATMAP_HOUR_LABELS has 12 entries", () => {
    expect(HEATMAP_HOUR_LABELS).toHaveLength(12);
  });
});

// ─── KpiCards ─────────────────────────────────────────────────────────────────

describe("KpiCards", () => {
  it("renders all KPI labels", () => {
    const kpis = getOverviewKpis();
    render(<KpiCards kpis={kpis} />);
    for (const kpi of kpis) {
      expect(screen.getByText(kpi.label)).toBeInTheDocument();
    }
  });

  it("renders KPI values", () => {
    const kpis = getOverviewKpis();
    render(<KpiCards kpis={kpis} />);
    expect(screen.getByText("18,240")).toBeInTheDocument();
  });

  it("renders trend text", () => {
    const kpis = getOverviewKpis();
    render(<KpiCards kpis={kpis} />);
    expect(screen.getByText("+12% vs yesterday")).toBeInTheDocument();
  });
});

// ─── FreshnessBanner ─────────────────────────────────────────────────────────

describe("FreshnessBanner", () => {
  it("shows stale warning when isStale=true", () => {
    render(
      <FreshnessBanner
        lastUpdatedAt="2026-04-23T11:00:00Z"
        isStale={true}
      />,
    );
    expect(screen.getByRole("alert")).toBeInTheDocument();
    expect(screen.getByText(/stale/i)).toBeInTheDocument();
  });

  it("shows quiet timestamp when isStale=false", () => {
    render(
      <FreshnessBanner
        lastUpdatedAt="2026-04-23T11:58:00Z"
        isStale={false}
      />,
    );
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
    expect(screen.getByText(/last updated/i)).toBeInTheDocument();
  });
});

// ─── TopCampaigns ─────────────────────────────────────────────────────────────

describe("TopCampaigns", () => {
  const rows = getTopCampaigns();

  it("renders campaign names", () => {
    render(<TopCampaigns rows={rows} />);
    expect(screen.getByText("Q1 product announcement")).toBeInTheDocument();
  });

  it("renders send counts", () => {
    render(<TopCampaigns rows={rows} />);
    expect(screen.getByText("12,847")).toBeInTheDocument();
  });

  it("renders open rates", () => {
    render(<TopCampaigns rows={rows} />);
    expect(screen.getByText("38.2%")).toBeInTheDocument();
  });

  it("renders — for zero open rate", () => {
    render(<TopCampaigns rows={rows} />);
    const dashes = screen.getAllByText("—");
    expect(dashes.length).toBeGreaterThan(0);
  });

  it("campaign name links to /campaigns/id", () => {
    render(<TopCampaigns rows={rows} />);
    const link = screen.getByRole("link", { name: "Q1 product announcement" });
    expect(link).toHaveAttribute("href", "/campaigns/cmp-004");
  });
});

// ─── TopFailingDomains ────────────────────────────────────────────────────────

describe("TopFailingDomains", () => {
  const domains = getDomainReputationData();

  it("renders failing domains with critical badge", () => {
    render(<TopFailingDomains domains={domains} />);
    expect(screen.getByText(/domains needing attention/i)).toBeInTheDocument();
  });

  it("shows critical badge for bad domain", () => {
    render(<TopFailingDomains domains={domains} />);
    expect(screen.getAllByText("critical").length).toBeGreaterThan(0);
  });

  it("shows all-clear message when no failing domains", () => {
    const clean = domains.map((d) => ({ ...d, riskLevel: "ok" as const }));
    render(<TopFailingDomains domains={clean} />);
    expect(screen.getByText(/all domains within thresholds/i)).toBeInTheDocument();
  });

  it("domain name links to /domains/id", () => {
    render(<TopFailingDomains domains={domains} />);
    const link = screen.getByRole("link", { name: /m49\.dispatch\.internal/ });
    expect(link).toHaveAttribute("href", "/domains/dom-003");
  });
});
