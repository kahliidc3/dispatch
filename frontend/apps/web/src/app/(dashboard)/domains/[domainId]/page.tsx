import Link from "next/link";
import { notFound } from "next/navigation";
import { Badge } from "@/components/ui/badge";
import { SectionPanel } from "@/components/patterns/section-panel";
import { formatTimestamp } from "@/lib/formatters";
import { getDomainDetail } from "../_lib/domains-queries";
import { CircuitBreakerBadges } from "../_components/circuit-breaker-badges";
import { DnsRecords } from "../_components/dns-records";
import { DomainRetireButton } from "../_components/domain-retire-button";
import { VerifyButton } from "../_components/verify-button";

const statusVariant = {
  pending: "muted",
  verifying: "warning",
  verified: "success",
  cooling: "warning",
  burnt: "danger",
  retired: "outline",
} as const;

type DomainDetailPageProps = {
  params: Promise<{ domainId: string }>;
};

export default async function DomainDetailPage({
  params,
}: DomainDetailPageProps) {
  const { domainId } = await params;
  const domain = getDomainDetail(domainId);

  if (!domain) notFound();

  return (
    <div className="page-stack">
      <header className="page-header">
        <div>
          <p className="text-sm text-text-muted">
            <Link href="/domains" className="hover:underline">
              Domains
            </Link>{" "}
            / {domain.name}
          </p>
          <h1 className="page-title">{domain.name}</h1>
        </div>
        <div className="page-actions">
          <VerifyButton domainId={domain.id} initialStatus={domain.status} />
          <DomainRetireButton domainId={domain.id} status={domain.status} />
        </div>
      </header>

      <SectionPanel title="Overview">
        <div className="summary-list">
          <div className="summary-row">
            <span className="text-sm font-medium">Status</span>
            <Badge variant={statusVariant[domain.status]}>{domain.status}</Badge>
          </div>
          <div className="summary-row">
            <span className="text-sm font-medium">Circuit breaker</span>
            <CircuitBreakerBadges state={domain.breaker} />
          </div>
          <div className="summary-row">
            <span className="text-sm font-medium">Created</span>
            <span className="text-sm text-text-muted">
              {formatTimestamp(domain.createdAt)}
            </span>
          </div>
          <div className="summary-row">
            <span className="text-sm font-medium">Last updated</span>
            <span className="text-sm text-text-muted">
              {formatTimestamp(domain.updatedAt)}
            </span>
          </div>
        </div>
      </SectionPanel>

      <SectionPanel>
        <DnsRecords records={domain.dnsRecords} />
      </SectionPanel>
    </div>
  );
}
