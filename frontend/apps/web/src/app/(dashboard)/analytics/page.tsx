import { EngagementCharts } from "./_components/engagement-charts";
import { KpiCards } from "./_components/kpi-cards";

export default function AnalyticsPage() {
  return (
    <div className="page-stack">
      <header className="page-header">
        <div>
          <h1 className="page-title">Analytics</h1>
          <p className="page-description">
            Overview dashboards, domain reputation, and engagement visuals land
            later. This scaffold reserves the routes and content slots.
          </p>
        </div>
      </header>
      <KpiCards />
      <EngagementCharts />
    </div>
  );
}
