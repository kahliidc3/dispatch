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

export type CampaignDraft = {
  name: string;
  tag: string;
  senderProfileId: string;
  templateId: string;
  templateVersion: number | null;
  audienceType: "segment" | "list";
  audienceId: string;
  scheduleType: "immediate" | "scheduled";
  scheduledAt: string;
  timezone: string;
};

export type PreflightSeverity = "ok" | "warning" | "critical";

export type PreflightCheck = {
  id: string;
  label: string;
  severity: PreflightSeverity;
  detail: string;
};

export const EMPTY_DRAFT: CampaignDraft = {
  name: "",
  tag: "",
  senderProfileId: "",
  templateId: "",
  templateVersion: null,
  audienceType: "segment",
  audienceId: "",
  scheduleType: "immediate",
  scheduledAt: "",
  timezone: "UTC",
};

export const WIZARD_STEPS = [
  "Details",
  "Sender",
  "Template",
  "Audience",
  "Schedule",
  "Review",
] as const;

export function isDraftStepComplete(
  step: number,
  draft: CampaignDraft,
): boolean {
  switch (step) {
    case 0:
      return draft.name.trim().length > 0;
    case 1:
      return draft.senderProfileId !== "";
    case 2:
      return draft.templateId !== "" && draft.templateVersion !== null;
    case 3:
      return draft.audienceId !== "";
    case 4:
      return draft.scheduleType === "immediate" || draft.scheduledAt !== "";
    default:
      return true;
  }
}
