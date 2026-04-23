export type CampaignStatus =
  | "draft"
  | "scheduled"
  | "running"
  | "paused"
  | "completed";

export type CampaignRecord = {
  id: string;
  name: string;
  audience: string;
  status: CampaignStatus;
  updatedAt: string;
};
