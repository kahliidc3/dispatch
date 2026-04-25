import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import type { DomainReputation, RiskLevel } from "../_lib/analytics-queries";

const riskVariant: Record<RiskLevel, "success" | "warning" | "danger"> = {
  ok: "success",
  warn: "warning",
  critical: "danger",
};

const breakerVariant: Record<
  DomainReputation["breakerState"],
  "success" | "danger" | "warning"
> = {
  closed: "success",
  open: "danger",
  "half-open": "warning",
};

type TopFailingDomainsProps = {
  domains: DomainReputation[];
};

export function TopFailingDomains({ domains }: TopFailingDomainsProps) {
  const failing = domains.filter((d) => d.riskLevel !== "ok");

  if (failing.length === 0) {
    return (
      <section className="surface-panel p-5">
        <h2 className="section-title mb-2">Domain health</h2>
        <p className="text-sm text-success">All domains within thresholds.</p>
      </section>
    );
  }

  return (
    <section className="surface-panel p-5">
      <h2 className="section-title mb-4">Domains needing attention</h2>
      <div className="grid gap-3">
        {failing.map((domain) => (
          <div
            key={domain.id}
            className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-border p-3"
          >
            <div className="min-w-0">
              <Link
                href={`/domains/${domain.id}`}
                className="mono text-sm font-medium hover:underline"
              >
                {domain.name}
              </Link>
              <p className="mt-0.5 text-xs text-text-muted">
                Bounce {domain.bounceRate.toFixed(2)}% · Complaint{" "}
                {domain.complaintRate.toFixed(3)}% · Delivery{" "}
                {domain.deliveryRate.toFixed(1)}%
              </p>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <Badge variant={riskVariant[domain.riskLevel]}>
                {domain.riskLevel}
              </Badge>
              <Badge variant={breakerVariant[domain.breakerState]}>
                {domain.breakerState}
              </Badge>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
