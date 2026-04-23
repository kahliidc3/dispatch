import { EmptyState } from "@/components/shared/empty-state";
import { DomainHealthGrid } from "./_components/domain-health-grid";

export default function DomainsPage() {
  return (
    <div className="page-stack">
      <header className="page-header">
        <div>
          <h1 className="page-title">Domains</h1>
          <p className="page-description">
            Manual verification and sender profile flows come later. The route,
            nested detail page, and baseline health table are scaffolded now.
          </p>
        </div>
      </header>
      <DomainHealthGrid />
      <EmptyState
        title="Provisioning workflow placeholder"
        description="Add-domain dialogs, DNS record views, and sender profile actions are deferred to later sprints."
      />
    </div>
  );
}
