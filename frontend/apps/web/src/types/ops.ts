export type BreakerScope = "domain" | "ip_pool" | "sender_profile" | "account";
export type BreakerEntryState = "open" | "closed" | "half_open";

export type BreakerEntry = {
  id: string;
  scope: BreakerScope;
  entityId: string;
  entityName: string;
  entityHref: string;
  state: BreakerEntryState;
  trippedAt: string | null;
  reason: string | null;
  bounceRatePct: number | null;
  complaintRatePct: number | null;
  autoResetAt: string | null;
  updatedAt: string;
};

export type BreakerTripEvent = {
  id: string;
  breakerId: string;
  type: "tripped" | "reset" | "auto_reset";
  occurredAt: string;
  actor: string | null;
  justification: string | null;
  bounceRatePct: number | null;
  complaintRatePct: number | null;
};

export type QueueRow = {
  domainId: string;
  domainName: string;
  queueName: string;
  workerCount: number;
  queueDepth: number;
  oldestQueuedAgeSeconds: number | null;
  denialsPerMinute: number;
  updatedAt: string;
};
