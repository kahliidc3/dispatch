import Link from "next/link";
import { DataTable } from "@/components/shared/data-table";
import { Badge } from "@/components/ui/badge";
import { formatTimestamp } from "@/lib/formatters";
import { domains } from "../_lib/domains-queries";
import { CircuitBreakerBadges } from "./circuit-breaker-badges";

const verificationVariant = {
  pending: "muted",
  verifying: "warning",
  verified: "success",
} as const;

const reputationVariant = {
  warming: "warning",
  healthy: "success",
  cooling: "outline",
} as const;

export function DomainHealthGrid() {
  return (
    <DataTable
      caption="Static placeholder data until domain APIs are wired"
      columns={[
        { key: "name", label: "Domain" },
        { key: "verification", label: "Verification" },
        { key: "reputation", label: "Reputation" },
        { key: "breaker", label: "Breaker" },
        { key: "updatedAt", label: "Updated", className: "text-right" },
      ]}
      rows={domains.map((domain) => ({
        name: (
          <Link href={`/domains/${domain.id}`} className="font-medium hover:underline">
            {domain.name}
          </Link>
        ),
        verification: (
          <Badge variant={verificationVariant[domain.verification]}>
            {domain.verification}
          </Badge>
        ),
        reputation: (
          <Badge variant={reputationVariant[domain.reputation]}>
            {domain.reputation}
          </Badge>
        ),
        breaker: <CircuitBreakerBadges state={domain.breaker} />,
        updatedAt: formatTimestamp(domain.updatedAt),
      }))}
    />
  );
}
