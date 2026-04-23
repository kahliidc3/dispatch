import { formatTimestamp } from "@/lib/formatters";
import { getDomainById } from "../_lib/domains-queries";
import { CircuitBreakerBadges } from "../_components/circuit-breaker-badges";

type DomainDetailPageProps = {
  params: Promise<{ domainId: string }>;
};

export default async function DomainDetailPage({
  params,
}: DomainDetailPageProps) {
  const { domainId } = await params;
  const domain = getDomainById(domainId);

  return (
    <div className="page-stack">
      <header className="page-header">
        <div>
          <h1 className="page-title">Domain detail</h1>
          <p className="page-description">
            DNS rows, verification polling, and sender profile binding land
            later. This page locks the route and the health summary layout.
          </p>
        </div>
      </header>

      <section className="surface-panel p-6">
        <div className="page-stack">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <h2 className="section-title">{domain.name}</h2>
              <p className="page-description">
                Updated {formatTimestamp(domain.updatedAt)}
              </p>
            </div>
            <CircuitBreakerBadges state={domain.breaker} />
          </div>
          <div className="summary-list">
            <div className="summary-row">
              <span className="text-sm font-medium">Verification</span>
              <span className="text-sm text-text-muted">
                {domain.verification}
              </span>
            </div>
            <div className="summary-row">
              <span className="text-sm font-medium">Reputation</span>
              <span className="text-sm text-text-muted">{domain.reputation}</span>
            </div>
            <div className="summary-row">
              <span className="text-sm font-medium">DNS workflow</span>
              <span className="text-sm text-text-muted">
                Placeholder only in Sprint 00
              </span>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
