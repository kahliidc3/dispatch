import type {
  BreakerEntry,
  BreakerScope,
  BreakerTripEvent,
  QueueRow,
} from "@/types/ops";

const QUEUE_DEPTH_WARN_THRESHOLD = 2000;

export { QUEUE_DEPTH_WARN_THRESHOLD };

// ─── Circuit Breaker Matrix ───────────────────────────────────────────────────

const breakerMatrix: BreakerEntry[] = [
  // Domain scope
  {
    id: "cbr-dom-001",
    scope: "domain",
    entityId: "dom-001",
    entityName: "m47.dispatch.internal",
    entityHref: "/domains/dom-001",
    state: "closed",
    trippedAt: null,
    reason: null,
    bounceRatePct: null,
    complaintRatePct: null,
    autoResetAt: null,
    updatedAt: "2026-04-24T09:58:00Z",
  },
  {
    id: "cbr-dom-002",
    scope: "domain",
    entityId: "dom-002",
    entityName: "m48.dispatch.internal",
    entityHref: "/domains/dom-002",
    state: "closed",
    trippedAt: null,
    reason: null,
    bounceRatePct: null,
    complaintRatePct: null,
    autoResetAt: null,
    updatedAt: "2026-04-24T09:58:00Z",
  },
  {
    id: "cbr-dom-003",
    scope: "domain",
    entityId: "dom-003",
    entityName: "m49.dispatch.internal",
    entityHref: "/domains/dom-003",
    state: "open",
    trippedAt: "2026-04-24T09:45:00Z",
    reason: "high_bounce_rate",
    bounceRatePct: 1.82,
    complaintRatePct: 0.02,
    autoResetAt: "2026-04-25T09:45:00Z",
    updatedAt: "2026-04-24T09:45:00Z",
  },
  // IP pool scope
  {
    id: "cbr-pool-001",
    scope: "ip_pool",
    entityId: "pool-001",
    entityName: "shared-pool-us-east",
    entityHref: "/sender-profiles",
    state: "closed",
    trippedAt: null,
    reason: null,
    bounceRatePct: null,
    complaintRatePct: null,
    autoResetAt: null,
    updatedAt: "2026-04-24T09:58:00Z",
  },
  {
    id: "cbr-pool-002",
    scope: "ip_pool",
    entityId: "pool-002",
    entityName: "dedicated-pool-us-east-01",
    entityHref: "/sender-profiles",
    state: "open",
    trippedAt: "2026-04-24T08:30:00Z",
    reason: "high_complaint_rate",
    bounceRatePct: 0.8,
    complaintRatePct: 0.09,
    autoResetAt: null,
    updatedAt: "2026-04-24T08:30:00Z",
  },
  // Sender profile scope
  {
    id: "cbr-sp-001",
    scope: "sender_profile",
    entityId: "sp-001",
    entityName: "Campaign broadcast",
    entityHref: "/sender-profiles/sp-001",
    state: "closed",
    trippedAt: null,
    reason: null,
    bounceRatePct: null,
    complaintRatePct: null,
    autoResetAt: null,
    updatedAt: "2026-04-24T09:58:00Z",
  },
  {
    id: "cbr-sp-002",
    scope: "sender_profile",
    entityId: "sp-002",
    entityName: "Transactional alerts",
    entityHref: "/sender-profiles/sp-002",
    state: "open",
    trippedAt: "2026-04-24T09:40:00Z",
    reason: "high_bounce_rate",
    bounceRatePct: 1.6,
    complaintRatePct: 0.03,
    autoResetAt: null,
    updatedAt: "2026-04-24T09:40:00Z",
  },
  // Account scope
  {
    id: "cbr-account",
    scope: "account",
    entityId: "account",
    entityName: "Platform account",
    entityHref: "/settings",
    state: "closed",
    trippedAt: null,
    reason: null,
    bounceRatePct: null,
    complaintRatePct: null,
    autoResetAt: null,
    updatedAt: "2026-04-24T09:58:00Z",
  },
];

const breakerTimelines: Record<string, BreakerTripEvent[]> = {
  "cbr-dom-003": [
    {
      id: "bte-dom-003-1",
      breakerId: "cbr-dom-003",
      type: "tripped",
      occurredAt: "2026-04-24T09:45:00Z",
      actor: null,
      justification: null,
      bounceRatePct: 1.82,
      complaintRatePct: 0.02,
    },
    {
      id: "bte-dom-003-2",
      breakerId: "cbr-dom-003",
      type: "reset",
      occurredAt: "2026-04-23T14:20:00Z",
      actor: "ali.amrani@dispatch.internal",
      justification: "Post-campaign cleanup — metrics confirmed clean for 2h.",
      bounceRatePct: null,
      complaintRatePct: null,
    },
    {
      id: "bte-dom-003-3",
      breakerId: "cbr-dom-003",
      type: "tripped",
      occurredAt: "2026-04-23T12:00:00Z",
      actor: null,
      justification: null,
      bounceRatePct: 1.92,
      complaintRatePct: 0.01,
    },
  ],
  "cbr-pool-002": [
    {
      id: "bte-pool-002-1",
      breakerId: "cbr-pool-002",
      type: "tripped",
      occurredAt: "2026-04-24T08:30:00Z",
      actor: null,
      justification: null,
      bounceRatePct: 0.8,
      complaintRatePct: 0.09,
    },
    {
      id: "bte-pool-002-2",
      breakerId: "cbr-pool-002",
      type: "reset",
      occurredAt: "2026-04-22T16:00:00Z",
      actor: "ali.amrani@dispatch.internal",
      justification: "Spam folder complaint surge resolved — offending segment removed.",
      bounceRatePct: null,
      complaintRatePct: null,
    },
  ],
  "cbr-sp-002": [
    {
      id: "bte-sp-002-1",
      breakerId: "cbr-sp-002",
      type: "tripped",
      occurredAt: "2026-04-24T09:40:00Z",
      actor: null,
      justification: null,
      bounceRatePct: 1.6,
      complaintRatePct: 0.03,
    },
  ],
};

export function getBreakerMatrix(): BreakerEntry[] {
  return breakerMatrix;
}

export function getBreakerTimeline(breakerId: string): BreakerTripEvent[] {
  return breakerTimelines[breakerId] ?? [];
}

export function getBreakerForEntity(
  scope: BreakerScope,
  entityId: string,
): BreakerEntry | null {
  return (
    breakerMatrix.find(
      (b) => b.scope === scope && b.entityId === entityId,
    ) ?? null
  );
}

export function getOpenBreakerCount(): number {
  return breakerMatrix.filter((b) => b.state === "open").length;
}

export function getQueueSnapshot(): QueueRow[] {
  return [
    {
      domainId: "dom-001",
      domainName: "m47.dispatch.internal",
      queueName: "send.m47.dispatch.internal",
      workerCount: 2,
      queueDepth: 0,
      oldestQueuedAgeSeconds: null,
      denialsPerMinute: 0,
      updatedAt: "2026-04-24T09:58:00Z",
    },
    {
      domainId: "dom-002",
      domainName: "m48.dispatch.internal",
      queueName: "send.m48.dispatch.internal",
      workerCount: 4,
      queueDepth: 1240,
      oldestQueuedAgeSeconds: 847,
      denialsPerMinute: 3.2,
      updatedAt: "2026-04-24T09:58:00Z",
    },
    {
      domainId: "dom-003",
      domainName: "m49.dispatch.internal",
      queueName: "send.m49.dispatch.internal",
      workerCount: 1,
      queueDepth: 5820,
      oldestQueuedAgeSeconds: 3601,
      denialsPerMinute: 14.7,
      updatedAt: "2026-04-24T09:58:00Z",
    },
  ];
}
