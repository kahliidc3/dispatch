import { CampaignsFilters } from "./_components/campaigns-filters";
import { CampaignsTable } from "./_components/campaigns-table";

export default function CampaignsPage() {
  return (
    <div className="page-stack">
      <header className="page-header">
        <div>
          <h1 className="page-title">Campaigns</h1>
          <p className="page-description">
            This placeholder reserves the campaign list surface and route
            structure for authoring, monitoring, and launch work in later
            sprints.
          </p>
        </div>
      </header>
      <CampaignsFilters />
      <CampaignsTable />
    </div>
  );
}
