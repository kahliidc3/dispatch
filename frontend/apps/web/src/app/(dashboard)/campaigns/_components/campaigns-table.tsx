import Link from "next/link";
import { DataTable } from "@/components/shared/data-table";
import { Badge } from "@/components/ui/badge";
import { formatTimestamp } from "@/lib/formatters";
import { campaigns } from "../_lib/campaigns-queries";

const statusVariant = {
  draft: "muted",
  scheduled: "warning",
  running: "success",
  paused: "outline",
  completed: "outline",
} as const;

export function CampaignsTable() {
  return (
    <DataTable
      caption="Static placeholder data until campaign APIs are wired"
      columns={[
        { key: "name", label: "Campaign" },
        { key: "audience", label: "Audience" },
        { key: "status", label: "Status" },
        { key: "updatedAt", label: "Updated", className: "text-right" },
      ]}
      rows={campaigns.map((campaign) => ({
        name: (
          <Link
            href={`/campaigns/${campaign.id}`}
            className="font-medium hover:underline"
          >
            {campaign.name}
          </Link>
        ),
        audience: campaign.audience,
        status: (
          <Badge variant={statusVariant[campaign.status]}>{campaign.status}</Badge>
        ),
        updatedAt: <span className="text-sm">{formatTimestamp(campaign.updatedAt)}</span>,
      }))}
    />
  );
}
