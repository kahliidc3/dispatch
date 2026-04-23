import { getCampaignById } from "../_lib/campaigns-queries";
import { CampaignHeader } from "./_components/campaign-header";
import { CampaignMetrics } from "./_components/campaign-metrics";

type CampaignDetailPageProps = {
  params: Promise<{ campaignId: string }>;
};

export default async function CampaignDetailPage({
  params,
}: CampaignDetailPageProps) {
  const { campaignId } = await params;
  const campaign = getCampaignById(campaignId);

  return (
    <div className="page-stack">
      <header className="page-header">
        <div>
          <h1 className="page-title">Campaign detail</h1>
          <p className="page-description">
            Monitoring and message inspection land in later sprints. This page
            locks the route and nested component structure now.
          </p>
        </div>
      </header>
      <CampaignHeader campaign={campaign} />
      <CampaignMetrics />
    </div>
  );
}
