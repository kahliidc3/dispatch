import type {
  CampaignRecord,
  CampaignDetail,
  CampaignMessage,
  CampaignMessageDetail,
  MessagesPage,
  PreflightCheck,
} from "@/types/campaign";

export const campaigns: CampaignRecord[] = [
  {
    id: "cmp-001",
    name: "April warmup cohort",
    audience: "Active newsletter subscribers",
    status: "draft",
    updatedAt: "2026-04-23T08:30:00Z",
  },
  {
    id: "cmp-002",
    name: "Suppression audit follow-up",
    audience: "API and webhook contacts",
    status: "scheduled",
    updatedAt: "2026-04-23T10:15:00Z",
  },
  {
    id: "cmp-003",
    name: "Seed inbox test",
    audience: "Recent openers or clickers",
    status: "running",
    updatedAt: "2026-04-23T11:05:00Z",
  },
  {
    id: "cmp-004",
    name: "Q1 product announcement",
    audience: "Active newsletter subscribers",
    status: "completed",
    updatedAt: "2026-03-15T14:00:00Z",
  },
  {
    id: "cmp-005",
    name: "Warmup pause test",
    audience: "API and webhook contacts",
    status: "paused",
    updatedAt: "2026-04-10T09:00:00Z",
  },
];

export function getCampaignById(campaignId: string): CampaignRecord {
  return campaigns.find((c) => c.id === campaignId) ?? campaigns[0]!;
}

// ─── Velocity ─────────────────────────────────────────────────────────────────

function buildVelocityPoints(count = 60): { label: string; value: number }[] {
  const now = new Date("2026-04-23T12:00:00Z");
  return Array.from({ length: count }, (_, i) => {
    const t = new Date(now.getTime() - (count - 1 - i) * 60_000);
    const hh = String(t.getUTCHours()).padStart(2, "0");
    const mm = String(t.getUTCMinutes()).padStart(2, "0");
    const base = 120 + Math.floor(Math.sin(i / 8) * 40);
    const jitter = Math.floor(Math.random() * 20) - 10;
    return { label: `${hh}:${mm}`, value: Math.max(0, base + jitter) };
  });
}

// ─── KPIs ─────────────────────────────────────────────────────────────────────

const DETAIL_MAP: Record<string, Omit<CampaignDetail, keyof CampaignRecord>> = {
  "cmp-003": {
    domainId: "dom-003",
    kpis: {
      queued: 1240,
      sending: 38,
      sent: 10842,
      delivered: 10710,
      bounced: 92,
      complained: 4,
      opened: 3284,
      clicked: 812,
    },
    velocityPoints: buildVelocityPoints(),
  },
  "cmp-004": {
    domainId: "dom-002",
    kpis: {
      queued: 0,
      sending: 0,
      sent: 12847,
      delivered: 12690,
      bounced: 112,
      complained: 8,
      opened: 4901,
      clicked: 1342,
    },
    velocityPoints: buildVelocityPoints().map((p) => ({ ...p, value: 0 })),
  },
};

export function getMockCampaignDetail(campaignId: string): CampaignDetail {
  const base = getCampaignById(campaignId);
  const extra = DETAIL_MAP[campaignId] ?? {
    domainId: "dom-002",
    kpis: {
      queued: 0,
      sending: 0,
      sent: 0,
      delivered: 0,
      bounced: 0,
      complained: 0,
      opened: 0,
      clicked: 0,
    },
    velocityPoints: buildVelocityPoints().map((p) => ({ ...p, value: 0 })),
  };
  return { ...base, ...extra };
}

// ─── Messages ─────────────────────────────────────────────────────────────────

const MESSAGE_STATUSES: import("@/types/campaign").MessageStatus[] = [
  "delivered",
  "delivered",
  "delivered",
  "delivered",
  "opened",
  "clicked",
  "bounced",
  "complained",
  "failed",
];

const MOCK_EMAILS = [
  "al***@example.com",
  "bo***@corp.io",
  "ca***@example.org",
  "da***@test.net",
  "em***@company.com",
  "fr***@example.com",
  "gr***@test.io",
  "ha***@example.net",
  "in***@corp.com",
  "ja***@example.com",
];

function buildMessages(campaignId: string, count = 50): CampaignMessage[] {
  return Array.from({ length: count }, (_, i) => {
    const status = MESSAGE_STATUSES[i % MESSAGE_STATUSES.length]!;
    return {
      id: `msg-${campaignId}-${String(i + 1).padStart(4, "0")}`,
      campaignId,
      email: MOCK_EMAILS[i % MOCK_EMAILS.length]!,
      status,
      lastEventAt: new Date(
        Date.now() - (count - i) * 45_000,
      ).toISOString(),
      hasBounce: status === "bounced",
      hasClick: status === "clicked",
      hasComplaint: status === "complained",
      sesMessageId:
        status !== "queued" && status !== "failed"
          ? `010f018e${String(i).padStart(8, "0")}`
          : null,
    };
  });
}

const MESSAGE_CACHE: Record<string, CampaignMessage[]> = {};

function getMessages(campaignId: string): CampaignMessage[] {
  if (!MESSAGE_CACHE[campaignId]) {
    MESSAGE_CACHE[campaignId] = buildMessages(campaignId);
  }
  return MESSAGE_CACHE[campaignId]!;
}

export function getMockMessagesPage(
  campaignId: string,
  cursor: string | null,
  statusFilter: string | null,
  pageSize = 20,
): MessagesPage {
  let all = getMessages(campaignId);
  if (statusFilter) {
    all = all.filter((m) => m.status === statusFilter);
  }
  const startIndex = cursor
    ? all.findIndex((m) => m.id === cursor) + 1
    : 0;
  const slice = all.slice(startIndex, startIndex + pageSize);
  const last = slice.at(-1);
  const nextCursor =
    last && startIndex + pageSize < all.length ? last.id : null;
  return { messages: slice, nextCursor };
}

// ─── Message detail ───────────────────────────────────────────────────────────

export function getMockMessageDetail(
  campaignId: string,
  messageId: string,
): CampaignMessageDetail | null {
  const msg = getMessages(campaignId).find((m) => m.id === messageId);
  if (!msg) return null;

  const events = buildEventTimeline(msg);

  return {
    ...msg,
    contactId: `contact-${messageId}`,
    senderProfileName: "Dispatch Platform <noreply@m48.dispatch.internal>",
    events,
    renderedHtml: msg.status !== "queued" && msg.status !== "failed"
      ? `<html><body style="font-family:sans-serif;padding:24px"><h1>Hello!</h1><p>This is a preview of the rendered email for message <code>${messageId}</code>.</p></body></html>`
      : null,
  };
}

function buildEventTimeline(msg: CampaignMessage): import("@/types/campaign").MessageEvent[] {
  const base = new Date(msg.lastEventAt).getTime();
  const events: import("@/types/campaign").MessageEvent[] = [
    {
      id: `${msg.id}-ev-1`,
      type: "queued",
      timestamp: new Date(base - 300_000).toISOString(),
      detail: "Message entered the send queue",
    },
  ];

  if (msg.status !== "queued") {
    events.push({
      id: `${msg.id}-ev-2`,
      type: "sent",
      timestamp: new Date(base - 240_000).toISOString(),
      detail: msg.sesMessageId ? `SES message ID: ${msg.sesMessageId}` : null,
    });
  }

  if (
    msg.status === "delivered" ||
    msg.status === "opened" ||
    msg.status === "clicked"
  ) {
    events.push({
      id: `${msg.id}-ev-3`,
      type: "delivered",
      timestamp: new Date(base - 180_000).toISOString(),
      detail: "Delivery confirmed by receiving MTA",
    });
  }

  if (msg.status === "opened" || msg.status === "clicked") {
    events.push({
      id: `${msg.id}-ev-4`,
      type: "opened",
      timestamp: new Date(base - 60_000).toISOString(),
      detail: "Tracking pixel loaded",
    });
  }

  if (msg.status === "clicked") {
    events.push({
      id: `${msg.id}-ev-5`,
      type: "clicked",
      timestamp: new Date(base).toISOString(),
      detail: "Link click recorded",
    });
  }

  if (msg.status === "bounced") {
    events.push({
      id: `${msg.id}-ev-3b`,
      type: "bounced",
      timestamp: new Date(base).toISOString(),
      detail: "Hard bounce — address does not exist (550 5.1.1)",
    });
  }

  if (msg.status === "complained") {
    events.push({
      id: `${msg.id}-ev-3c`,
      type: "complained",
      timestamp: new Date(base).toISOString(),
      detail: "Spam complaint via FBL — address suppressed",
    });
  }

  if (msg.status === "failed") {
    events.push({
      id: `${msg.id}-ev-2f`,
      type: "failed",
      timestamp: new Date(base).toISOString(),
      detail: "Send failed — circuit breaker open at send time",
    });
  }

  return events;
}

// ─── Pre-flight ───────────────────────────────────────────────────────────────

export function getMockPreflightChecks(audienceCount: number): PreflightCheck[] {
  return [
    {
      id: "suppression",
      label: "Suppression exclusion estimate",
      severity: audienceCount > 1000 ? "warning" : "ok",
      detail:
        audienceCount > 1000
          ? `~${Math.round(audienceCount * 0.03).toLocaleString()} addresses will be excluded`
          : "Exclusion count within normal range",
    },
    {
      id: "domain_breaker",
      label: "Domain circuit breaker",
      severity: "ok",
      detail: "All sending domains reporting closed",
    },
    {
      id: "sender_status",
      label: "Sender profile status",
      severity: "ok",
      detail: "Sender profile is active",
    },
    {
      id: "account_breaker",
      label: "Account-level circuit breaker",
      severity: "ok",
      detail: "Account breaker closed — sends are allowed",
    },
    {
      id: "spam_score",
      label: "Spam score estimate",
      severity: "ok",
      detail: "Score: 0.0 (gate 7 stub — ML scorer deferred to Sprint 17)",
    },
  ];
}
