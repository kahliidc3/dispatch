import type { CampaignRecord, PreflightCheck } from "@/types/campaign";

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
