import Link from "next/link";
import { DataTable } from "@/components/shared/data-table";
import { Badge } from "@/components/ui/badge";
import { formatTimestamp } from "@/lib/formatters";
import type { DomainStatus } from "@/types/domain";
import { domainList } from "../_lib/domains-queries";
import { CircuitBreakerBadges } from "./circuit-breaker-badges";

const statusVariant: Record<
  DomainStatus,
  "muted" | "warning" | "success" | "danger" | "outline"
> = {
  pending: "muted",
  verifying: "warning",
  verified: "success",
  cooling: "warning",
  burnt: "danger",
  retired: "outline",
};

export function DomainHealthGrid() {
  return (
    <DataTable
      caption="Sending domains"
      columns={[
        { key: "name", label: "Domain" },
        { key: "status", label: "Status" },
        { key: "breaker", label: "Breaker" },
        { key: "updatedAt", label: "Updated", className: "text-right" },
      ]}
      rows={domainList.map((domain) => ({
        name: (
          <Link href={`/domains/${domain.id}`} className="font-medium hover:underline">
            {domain.name}
          </Link>
        ),
        status: (
          <Badge variant={statusVariant[domain.status]}>{domain.status}</Badge>
        ),
        breaker: <CircuitBreakerBadges state={domain.breaker} />,
        updatedAt: formatTimestamp(domain.updatedAt),
      }))}
    />
  );
}
