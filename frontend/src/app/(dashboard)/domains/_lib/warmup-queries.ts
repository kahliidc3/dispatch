import type {
  WarmupDay,
  WarmupPreset,
  WarmupSchedule,
  WarmupStatus,
  PostmasterData,
  PostmasterReputation,
} from "@/types/domain";

// ─── Schedule cap tables ──────────────────────────────────────────────────────

export const STANDARD_CAPS: number[] = [
  50,  100, 150, 200,  300,  400,  500,  600,  700,  800,
  900, 1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800,
  2000, 2200, 2400, 2600, 2800, 3000, 3200, 3400, 3600, 4000,
];

export const CONSERVATIVE_CAPS: number[] = [
  50,  50,  50,  100, 100, 100, 150, 150, 200, 200,
  250, 250, 300, 350, 400, 450, 500, 550, 600, 650,
  700, 750, 800, 850, 900, 1000, 1100, 1200, 1300, 1400,
  1500, 1600, 1700, 1800, 1900, 2000, 2200, 2400, 2600, 2800,
  3000, 3200, 3400, 3600, 4000,
];

export const AGGRESSIVE_CAPS: number[] = [
  500,  800, 1100, 1400, 1700, 2000, 2300, 2600, 2900, 3200,
  3500, 3800, 4000, 4000, 4000, 4000, 4000, 4000, 4000, 4000,
  4000,
];

export const PRESET_TOTAL_DAYS: Record<Exclude<WarmupPreset, "custom">, number> = {
  conservative: CONSERVATIVE_CAPS.length,
  standard: STANDARD_CAPS.length,
  aggressive: AGGRESSIVE_CAPS.length,
};

export function capsForPreset(preset: WarmupPreset): number[] {
  if (preset === "conservative") return CONSERVATIVE_CAPS;
  if (preset === "aggressive") return AGGRESSIVE_CAPS;
  return STANDARD_CAPS;
}

function buildSchedule(
  preset: WarmupPreset,
  caps: number[],
  currentDay: number,
  actualSendsMap: Record<number, number>,
): WarmupSchedule {
  const days: WarmupDay[] = caps.map((cap, i) => ({
    day: i + 1,
    cap,
    actualSends: i < currentDay ? (actualSendsMap[i + 1] ?? cap) : null,
  }));
  return { preset, totalDays: caps.length, days };
}

// ─── Mock warmup status ───────────────────────────────────────────────────────

const dom001ActualSends: Record<number, number> = {};

const dom002ActualSends: Record<number, number> = {
  1: 48, 2: 95, 3: 141, 4: 187, 5: 290, 6: 382, 7: 471, 8: 573,
  9: 680, 10: 776, 11: 855, 12: 960, 13: 1050, 14: 1140, 15: 1220,
  16: 1330, 17: 1421, 18: 1509, 19: 1620, 20: 1730, 21: 1890, 22: 2100,
  23: 2280,
};

const dom003ActualSends: Record<number, number> = {
  1: 52, 2: 104, 3: 157, 4: 212, 5: 310, 6: 415, 7: 520, 8: 615,
  9: 700, 10: 810,
};

const warmupData: Record<string, WarmupStatus> = {
  "dom-001": {
    domainId: "dom-001",
    lifecycle: "warming",
    currentDay: 0,
    totalDays: 30,
    todayCap: 50,
    todaySends: 0,
    scheduledGraduationAt: null,
    graduatedAt: null,
    schedule: buildSchedule("standard", STANDARD_CAPS, 0, dom001ActualSends),
  },
  "dom-002": {
    domainId: "dom-002",
    lifecycle: "warming",
    currentDay: 23,
    totalDays: 30,
    todayCap: 2600,
    todaySends: 2140,
    scheduledGraduationAt: "2026-04-30T00:00:00Z",
    graduatedAt: null,
    schedule: buildSchedule("standard", STANDARD_CAPS, 23, dom002ActualSends),
  },
  "dom-003": {
    domainId: "dom-003",
    lifecycle: "warming",
    currentDay: 11,
    totalDays: 30,
    todayCap: 900,
    todaySends: 1050,
    scheduledGraduationAt: null,
    graduatedAt: null,
    schedule: buildSchedule("standard", STANDARD_CAPS, 11, dom003ActualSends),
  },
};

export function getWarmupStatus(domainId: string): WarmupStatus | null {
  return warmupData[domainId] ?? null;
}

// ─── Mock Postmaster data ─────────────────────────────────────────────────────

function reputationLabel(day: number, base: PostmasterReputation): PostmasterReputation {
  return base;
}

const dom002PostmasterMetrics = Array.from({ length: 7 }, (_, i) => {
  const d = new Date("2026-04-18T00:00:00Z");
  d.setDate(d.getDate() + i);
  return {
    date: d.toISOString().slice(0, 10),
    spamRatePct: 0.01 + i * 0.002,
    domainReputation: reputationLabel(i, "high") as PostmasterReputation,
    spfPassPct: 99.1 + (i % 3) * 0.1,
    dkimPassPct: 98.8 + (i % 2) * 0.2,
    dmarcPassPct: 98.5 + (i % 4) * 0.1,
  };
});

const dom003PostmasterMetrics = Array.from({ length: 7 }, (_, i) => {
  const d = new Date("2026-04-18T00:00:00Z");
  d.setDate(d.getDate() + i);
  const reputations: PostmasterReputation[] = ["medium", "medium", "low", "medium", "medium", "low", "medium"];
  return {
    date: d.toISOString().slice(0, 10),
    spamRatePct: 0.4 + i * 0.06,
    domainReputation: reputations[i]!,
    spfPassPct: 91.0 - i * 0.5,
    dkimPassPct: 88.3 - i * 0.8,
    dmarcPassPct: 85.0 - i * 0.4,
  };
});

const postmasterData: Record<string, PostmasterData> = {
  "dom-001": {
    domainId: "dom-001",
    connected: false,
    asOf: null,
    metrics: [],
  },
  "dom-002": {
    domainId: "dom-002",
    connected: true,
    asOf: "2026-04-24T06:00:00Z",
    metrics: dom002PostmasterMetrics,
  },
  "dom-003": {
    domainId: "dom-003",
    connected: true,
    asOf: "2026-04-24T06:00:00Z",
    metrics: dom003PostmasterMetrics,
  },
};

export function getPostmasterData(domainId: string): PostmasterData {
  return (
    postmasterData[domainId] ?? {
      domainId,
      connected: false,
      asOf: null,
      metrics: [],
    }
  );
}

// ─── Warming domains (for analytics widget) ───────────────────────────────────

export type WarmingDomainRow = {
  id: string;
  name: string;
  currentDay: number;
  totalDays: number;
  todayCap: number;
  todaySends: number;
  pctComplete: number;
};

const domainNames: Record<string, string> = {
  "dom-001": "m47.dispatch.internal",
  "dom-002": "m48.dispatch.internal",
  "dom-003": "m49.dispatch.internal",
};

export function getWarmingDomains(): WarmingDomainRow[] {
  return Object.values(warmupData)
    .filter((w) => w.lifecycle === "warming")
    .map((w) => ({
      id: w.domainId,
      name: domainNames[w.domainId] ?? w.domainId,
      currentDay: w.currentDay,
      totalDays: w.totalDays,
      todayCap: w.todayCap,
      todaySends: w.todaySends,
      pctComplete: Math.round((w.currentDay / w.totalDays) * 100),
    }));
}
