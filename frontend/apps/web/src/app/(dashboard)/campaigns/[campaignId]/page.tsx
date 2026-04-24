import { notFound } from "next/navigation";
import { campaigns } from "../_lib/campaigns-queries";
import {
  getMockCampaignDetail,
  getMockMessagesPage,
} from "../_lib/campaigns-queries";
import { CampaignMonitor } from "./_components/campaign-monitor";

type CampaignDetailPageProps = {
  params: Promise<{ campaignId: string }>;
};

export default async function CampaignDetailPage({
  params,
}: CampaignDetailPageProps) {
  const { campaignId } = await params;

  const exists = campaigns.find((c) => c.id === campaignId);
  if (!exists) notFound();

  const detail = getMockCampaignDetail(campaignId);
  const initialPage = getMockMessagesPage(campaignId, null, null);

  return (
    <div className="page-stack">
      <header className="page-header">
        <div>
          <h1 className="page-title">Campaign monitoring</h1>
        </div>
      </header>
      <CampaignMonitor initialDetail={detail} initialPage={initialPage} />
    </div>
  );
}
