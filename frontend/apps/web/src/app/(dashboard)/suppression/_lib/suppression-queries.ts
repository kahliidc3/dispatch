import type {
  SuppressionEntry,
  SuppressionReason,
  SuppressionSource,
  SuppressionSyncStatus,
} from "@/types/suppression";

function entry(
  id: string,
  email: string,
  reason: SuppressionReason,
  source: SuppressionSource,
  createdAt: string,
  note: string | null = null,
): SuppressionEntry {
  return { id, email, reason, source, note, createdAt };
}

export const mockSuppressionList: SuppressionEntry[] = [
  entry("sup-001", "hard.bounce1@example.com", "hard_bounce", "ses_event", "2026-04-23T06:30:00Z"),
  entry("sup-002", "spam.complaint1@example.com", "spam_complaint", "ses_event", "2026-04-22T20:10:00Z"),
  entry("sup-003", "unsubscribed1@example.com", "unsubscribe", "one_click", "2026-04-21T14:00:00Z"),
  entry("sup-004", "manual.add@example.com", "manual", "manual", "2026-04-20T10:00:00Z", "Requested removal by user"),
  entry("sup-005", "hard.bounce2@example.com", "hard_bounce", "ses_event", "2026-04-20T08:00:00Z"),
  entry("sup-006", "soft.bounce1@acme.com", "soft_bounce", "ses_event", "2026-04-19T16:00:00Z"),
  entry("sup-007", "unsubscribed2@acme.com", "unsubscribe", "one_click", "2026-04-19T12:00:00Z"),
  entry("sup-008", "spam.complaint2@corp.io", "spam_complaint", "ses_event", "2026-04-18T09:00:00Z"),
  entry("sup-009", "hard.bounce3@corp.io", "hard_bounce", "ses_event", "2026-04-17T20:00:00Z"),
  entry("sup-010", "api.suppressed@partner.net", "manual", "api", "2026-04-17T11:00:00Z", "API bulk add"),
  entry("sup-011", "csv.imported1@partner.net", "manual", "csv_import", "2026-04-16T10:00:00Z"),
  entry("sup-012", "unsubscribed3@newsletter.co", "unsubscribe", "one_click", "2026-04-15T14:30:00Z"),
  entry("sup-013", "hard.bounce4@newsletter.co", "hard_bounce", "ses_event", "2026-04-14T08:00:00Z"),
  entry("sup-014", "spam.complaint3@sample.org", "spam_complaint", "ses_event", "2026-04-13T17:00:00Z"),
  entry("sup-015", "soft.bounce2@sample.org", "soft_bounce", "ses_event", "2026-04-12T10:00:00Z"),
  entry("sup-016", "unsubscribed4@example.com", "unsubscribe", "one_click", "2026-04-11T09:00:00Z"),
  entry("sup-017", "hard.bounce5@example.com", "hard_bounce", "ses_event", "2026-04-10T15:00:00Z"),
  entry("sup-018", "manual.bulk1@example.com", "manual", "csv_import", "2026-04-09T11:00:00Z"),
  entry("sup-019", "manual.bulk2@example.com", "manual", "csv_import", "2026-04-09T11:00:00Z"),
  entry("sup-020", "manual.bulk3@example.com", "manual", "csv_import", "2026-04-09T11:00:00Z"),
  entry("sup-021", "spam.complaint4@test.dev", "spam_complaint", "ses_event", "2026-04-08T08:00:00Z"),
  entry("sup-022", "hard.bounce6@test.dev", "hard_bounce", "ses_event", "2026-04-07T20:00:00Z"),
  entry("sup-023", "api.add2@internal.io", "manual", "api", "2026-04-06T10:00:00Z"),
  entry("sup-024", "unsubscribed5@internal.io", "unsubscribe", "one_click", "2026-04-05T16:00:00Z"),
  entry("sup-025", "soft.bounce3@internal.io", "soft_bounce", "ses_event", "2026-04-04T14:00:00Z"),
];

export const mockSyncStatus: SuppressionSyncStatus = {
  lastSyncAt: "2026-04-24T07:00:00Z",
  driftCount: 2,
};
