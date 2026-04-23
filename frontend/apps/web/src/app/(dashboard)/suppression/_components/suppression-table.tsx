import { DataTable } from "@/components/shared/data-table";
import { Badge } from "@/components/ui/badge";
import { formatTimestamp, maskEmailAddress } from "@/lib/formatters";

const suppressionRows = [
  {
    email: "reply.stop@example.com",
    reason: "unsubscribe",
    source: "one_click",
    createdAt: "2026-04-23T06:30:00Z",
  },
  {
    email: "bounce.hard@example.com",
    reason: "hard_bounce",
    source: "ses_event",
    createdAt: "2026-04-22T20:10:00Z",
  },
];

export function SuppressionTable() {
  return (
    <DataTable
      caption="Static suppression placeholder"
      columns={[
        { key: "email", label: "Email" },
        { key: "reason", label: "Reason" },
        { key: "source", label: "Source" },
        { key: "createdAt", label: "Created", className: "text-right" },
      ]}
      rows={suppressionRows.map((entry) => ({
        email: maskEmailAddress(entry.email),
        reason: <Badge variant="warning">{entry.reason}</Badge>,
        source: entry.source,
        createdAt: formatTimestamp(entry.createdAt),
      }))}
    />
  );
}
