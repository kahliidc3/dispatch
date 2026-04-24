import { CampaignWizard } from "./_components/campaign-wizard";

export default function CampaignCreatePage() {
  return (
    <div className="page-stack">
      <header className="page-header">
        <div>
          <h1 className="page-title">Create campaign</h1>
          <p className="page-description">
            Build and launch a campaign in a few steps.
          </p>
        </div>
      </header>
      <CampaignWizard />
    </div>
  );
}
