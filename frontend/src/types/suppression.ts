export type SuppressionReason =
  | "hard_bounce"
  | "soft_bounce"
  | "spam_complaint"
  | "unsubscribe"
  | "manual";

export type SuppressionSource =
  | "ses_event"
  | "one_click"
  | "csv_import"
  | "api"
  | "manual";

export type SuppressionEntry = {
  id: string;
  email: string;
  reason: SuppressionReason;
  source: SuppressionSource;
  note: string | null;
  createdAt: string;
};

export type SuppressionSyncStatus = {
  lastSyncAt: string | null;
  driftCount: number;
};

export const SUPPRESSION_REASON_LABELS: Record<SuppressionReason, string> = {
  hard_bounce: "Hard bounce",
  soft_bounce: "Soft bounce",
  spam_complaint: "Spam complaint",
  unsubscribe: "Unsubscribe",
  manual: "Manual",
};

export const SUPPRESSION_SOURCE_LABELS: Record<SuppressionSource, string> = {
  ses_event: "SES event",
  one_click: "One-click",
  csv_import: "CSV import",
  api: "API",
  manual: "Manual",
};

export const SUPPRESSION_REASON_VARIANTS: Record<
  SuppressionReason,
  "danger" | "warning" | "muted"
> = {
  hard_bounce: "danger",
  spam_complaint: "danger",
  soft_bounce: "warning",
  unsubscribe: "warning",
  manual: "muted",
};
