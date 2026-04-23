import { Badge } from "@/components/ui/badge";
import { formatTimestamp } from "@/lib/formatters";
import type { CampaignRecord } from "@/types/campaign";

const statusVariant = {
  draft: "muted",
  scheduled: "warning",
  running: "success",
  paused: "outline",
  completed: "outline",
} as const;

type CampaignHeaderProps = {
  campaign: CampaignRecord;
};

export function CampaignHeader({ campaign }: CampaignHeaderProps) {
  return (
    <section className="surface-panel p-6">
      <div className="page-stack">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h2 className="section-title">{campaign.name}</h2>
            <p className="page-description">{campaign.audience}</p>
          </div>
          <Badge variant={statusVariant[campaign.status]}>{campaign.status}</Badge>
        </div>
        <div className="summary-list">
          <div className="summary-row">
            <span className="text-sm font-medium">Campaign id</span>
            <span className="mono text-sm text-text-muted">{campaign.id}</span>
          </div>
          <div className="summary-row">
            <span className="text-sm font-medium">Last updated</span>
            <span className="text-sm text-text-muted">
              {formatTimestamp(campaign.updatedAt)}
            </span>
          </div>
        </div>
      </div>
    </section>
  );
}
