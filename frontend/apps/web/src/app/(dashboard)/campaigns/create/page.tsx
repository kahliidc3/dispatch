import { CampaignForm } from "./_components/campaign-form";
import { LaunchActions } from "./_components/launch-actions";

export default function CampaignCreatePage() {
  return (
    <div className="page-stack">
      <header className="page-header">
        <div>
          <h1 className="page-title">Create campaign</h1>
          <p className="page-description">
            Wizard orchestration is deferred. Sprint 00 reserves the nested
            route and placeholder composition for the future authoring flow.
          </p>
        </div>
      </header>
      <CampaignForm />
      <LaunchActions />
    </div>
  );
}
