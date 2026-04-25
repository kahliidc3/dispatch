import {
  getAnalyticsMeta,
  getOverviewKpis,
  getTopCampaigns,
  getDomainReputationData,
  getEngagementTimeSeries,
  getOpenRateHeatmap,
} from "./_lib/analytics-queries";
import { getWarmingDomains } from "@/app/(dashboard)/domains/_lib/warmup-queries";
import { FreshnessBanner } from "./_components/freshness-banner";
import { KpiCards } from "./_components/kpi-cards";
import { TopCampaigns } from "./_components/top-campaigns";
import { TopFailingDomains } from "./_components/top-failing-domains";
import { EngagementCharts } from "./_components/engagement-charts";
import { WarmingDomains } from "./_components/warming-domains";

export default function AnalyticsPage() {
  const meta = getAnalyticsMeta();
  const kpis = getOverviewKpis();
  const topCampaigns = getTopCampaigns();
  const domains = getDomainReputationData();
  const timeSeries = getEngagementTimeSeries();
  const heatmapCells = getOpenRateHeatmap();
  const warmingDomains = getWarmingDomains();

  return (
    <div className="page-stack">
      <header className="page-header">
        <div>
          <h1 className="page-title">Analytics</h1>
          <p className="page-description">
            Account-wide send metrics, engagement trends, and domain health.
          </p>
        </div>
      </header>

      <FreshnessBanner
        lastUpdatedAt={meta.lastUpdatedAt}
        isStale={meta.isStale}
      />

      <KpiCards kpis={kpis} />

      <div className="grid gap-4 xl:grid-cols-2">
        <TopCampaigns rows={topCampaigns} />
        <TopFailingDomains domains={domains} />
      </div>

      <WarmingDomains domains={warmingDomains} />

      <EngagementCharts timeSeries={timeSeries} heatmapCells={heatmapCells} />
    </div>
  );
}
