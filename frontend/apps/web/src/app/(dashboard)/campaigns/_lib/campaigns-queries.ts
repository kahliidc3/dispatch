import type { CampaignRecord } from "@/types/campaign";

export const campaigns: CampaignRecord[] = [
  {
    id: "cmp-001",
    name: "April warmup cohort",
    audience: "Founders · EMEA",
    status: "draft",
    updatedAt: "2026-04-23T08:30:00Z",
  },
  {
    id: "cmp-002",
    name: "Suppression audit follow-up",
    audience: "Recovered leads",
    status: "scheduled",
    updatedAt: "2026-04-23T10:15:00Z",
  },
  {
    id: "cmp-003",
    name: "Seed inbox test",
    audience: "Ops monitors",
    status: "running",
    updatedAt: "2026-04-23T11:05:00Z",
  },
];

export function getCampaignById(campaignId: string) {
  return campaigns.find((campaign) => campaign.id === campaignId) ?? campaigns[0];
}
