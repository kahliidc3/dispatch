// Bounce warn/critical thresholds (50% / 100% of backend limits)
const BOUNCE_WARN = 0.75;
const BOUNCE_CRITICAL = 1.5;
const COMPLAINT_WARN = 0.025;
const COMPLAINT_CRITICAL = 0.05;

export type RiskLevel = "ok" | "warn" | "critical";

export type OverviewKpi = {
  label: string;
  value: string;
  trend: "up" | "down" | "neutral";
  trendValue: string;
  trendPositive: boolean;
};

export type TopCampaignRow = {
  id: string;
  name: string;
  sends: number;
  openRate: number;
  sparkline: number[];
};

export type DomainReputation = {
  id: string;
  name: string;
  bounceRate: number;
  complaintRate: number;
  deliveryRate: number;
  breakerState: "open" | "closed" | "half-open";
  warmupStage: string;
  riskLevel: RiskLevel;
};

export type TimeSeriesPoint = {
  label: string;
  sent: number;
  delivered: number;
  bounced: number;
};

export type AnalyticsMeta = {
  lastUpdatedAt: string;
  isStale: boolean;
};

// ─── Meta ──────────────────────────────────────────────────────────────────────

export function getAnalyticsMeta(): AnalyticsMeta {
  const updatedAt = new Date("2026-04-23T11:58:00Z");
  const now = new Date("2026-04-23T12:00:00Z");
  const ageMs = now.getTime() - updatedAt.getTime();
  return {
    lastUpdatedAt: updatedAt.toISOString(),
    isStale: ageMs > 5 * 60 * 1000,
  };
}

// ─── Overview KPIs ────────────────────────────────────────────────────────────

export function getOverviewKpis(): OverviewKpi[] {
  return [
    {
      label: "Sends today",
      value: "18,240",
      trend: "up",
      trendValue: "+12% vs yesterday",
      trendPositive: true,
    },
    {
      label: "7-day sends",
      value: "98,412",
      trend: "up",
      trendValue: "+8% vs prior week",
      trendPositive: true,
    },
    {
      label: "Bounce rate",
      value: "0.42%",
      trend: "down",
      trendValue: "−0.06pp",
      trendPositive: true,
    },
    {
      label: "Complaint rate",
      value: "0.01%",
      trend: "neutral",
      trendValue: "No change",
      trendPositive: true,
    },
    {
      label: "Open rate",
      value: "37.8%",
      trend: "up",
      trendValue: "+1.2pp",
      trendPositive: true,
    },
    {
      label: "Click rate",
      value: "6.3%",
      trend: "down",
      trendValue: "−0.4pp",
      trendPositive: false,
    },
  ];
}

// ─── Top campaigns ────────────────────────────────────────────────────────────

export function getTopCampaigns(): TopCampaignRow[] {
  return [
    {
      id: "cmp-004",
      name: "Q1 product announcement",
      sends: 12847,
      openRate: 38.2,
      sparkline: [320, 410, 1820, 3200, 4100, 2890, 107],
    },
    {
      id: "cmp-003",
      name: "Seed inbox test",
      sends: 10842,
      openRate: 30.3,
      sparkline: [0, 0, 840, 2100, 3200, 3100, 1602],
    },
    {
      id: "cmp-002",
      name: "Suppression audit follow-up",
      sends: 4200,
      openRate: 41.0,
      sparkline: [0, 0, 0, 0, 4200, 0, 0],
    },
    {
      id: "cmp-001",
      name: "April warmup cohort",
      sends: 840,
      openRate: 0,
      sparkline: [0, 0, 0, 0, 0, 0, 0],
    },
    {
      id: "cmp-005",
      name: "Warmup pause test",
      sends: 620,
      openRate: 22.1,
      sparkline: [0, 90, 200, 240, 90, 0, 0],
    },
  ];
}

// ─── Domain reputation ────────────────────────────────────────────────────────

function riskLevel(bounceRate: number, complaintRate: number): RiskLevel {
  if (bounceRate >= BOUNCE_CRITICAL || complaintRate >= COMPLAINT_CRITICAL)
    return "critical";
  if (bounceRate >= BOUNCE_WARN || complaintRate >= COMPLAINT_WARN)
    return "warn";
  return "ok";
}

export function getDomainReputationData(): DomainReputation[] {
  return [
    {
      id: "dom-002",
      name: "m48.dispatch.internal",
      bounceRate: 0.42,
      complaintRate: 0.01,
      deliveryRate: 99.2,
      breakerState: "closed",
      warmupStage: "Stage 4 / 5",
      riskLevel: riskLevel(0.42, 0.01),
    },
    {
      id: "dom-003",
      name: "m49.dispatch.internal",
      bounceRate: 1.62,
      complaintRate: 0.06,
      deliveryRate: 96.1,
      breakerState: "open",
      warmupStage: "Stage 2 / 5",
      riskLevel: riskLevel(1.62, 0.06),
    },
    {
      id: "dom-001",
      name: "m47.dispatch.internal",
      bounceRate: 0.0,
      complaintRate: 0.0,
      deliveryRate: 0.0,
      breakerState: "closed",
      warmupStage: "Not started",
      riskLevel: riskLevel(0.0, 0.0),
    },
  ];
}

// ─── Time series ──────────────────────────────────────────────────────────────

export function getEngagementTimeSeries(): TimeSeriesPoint[] {
  const days = [
    "Apr 10", "Apr 11", "Apr 12", "Apr 13", "Apr 14",
    "Apr 15", "Apr 16", "Apr 17", "Apr 18", "Apr 19",
    "Apr 20", "Apr 21", "Apr 22", "Apr 23",
  ];
  const base = [
    4200, 5100, 6800, 7200, 9400,
    8800, 7600, 10200, 11400, 12800,
    14200, 15600, 16800, 18240,
  ];
  return days.map((label, i) => {
    const sent = base[i]!;
    const delivered = Math.round(sent * (0.985 + Math.random() * 0.01));
    const bounced = sent - delivered - Math.floor(sent * 0.002);
    return { label, sent, delivered, bounced: Math.max(0, bounced) };
  });
}

// ─── Open rate heatmap ────────────────────────────────────────────────────────
// 7 rows = Sun–Sat, 12 cols = 2-hour buckets (00:00–22:00)

export function getOpenRateHeatmap(): number[][] {
  const days = 7;
  const slots = 12;
  return Array.from({ length: days }, (_, d) =>
    Array.from({ length: slots }, (_, h) => {
      const isBusiness = d >= 1 && d <= 5 && h >= 4 && h <= 8;
      const isEvening = h >= 9 && h <= 10;
      const base = isBusiness ? 38 : isEvening ? 30 : 15;
      return Math.round(base + (Math.random() * 10 - 5));
    }),
  );
}

export const HEATMAP_HOUR_LABELS = [
  "00:00", "02:00", "04:00", "06:00", "08:00", "10:00",
  "12:00", "14:00", "16:00", "18:00", "20:00", "22:00",
];

export const HEATMAP_DAY_LABELS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
