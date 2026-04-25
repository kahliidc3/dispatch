"use client";

import Link from "next/link";
import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { DataTable } from "@/components/shared/data-table";
import { EmptyState } from "@/components/shared/empty-state";
import { formatTimestamp } from "@/lib/formatters";
import type { DomainListItem, DomainStatus } from "@/types/domain";
import { AddDomainDialog } from "./add-domain-dialog";
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

type DomainsTableProps = {
  initialDomains: DomainListItem[];
};

export function DomainsTable({ initialDomains }: DomainsTableProps) {
  const [domains, setDomains] = useState(initialDomains);

  function handleDomainAdded(domain: DomainListItem) {
    setDomains((prev) => [domain, ...prev]);
  }

  if (domains.length === 0) {
    return (
      <EmptyState
        title="No domains yet"
        description="Add a sending domain to get the DNS records and start verification."
        action={<AddDomainDialog onAdded={handleDomainAdded} />}
      />
    );
  }

  return (
    <DataTable
      caption="Sending domains"
      columns={[
        { key: "name", label: "Domain" },
        { key: "status", label: "Status" },
        { key: "breaker", label: "Circuit breaker" },
        { key: "updatedAt", label: "Updated", className: "text-right" },
      ]}
      rows={domains.map((domain) => ({
        name: (
          <Link
            href={`/domains/${domain.id}`}
            className="font-medium hover:underline"
          >
            {domain.name}
          </Link>
        ),
        status: (
          <Badge variant={statusVariant[domain.status]}>{domain.status}</Badge>
        ),
        breaker: <CircuitBreakerBadges state={domain.breaker} />,
        updatedAt: (
          <span className="text-text-muted">{formatTimestamp(domain.updatedAt)}</span>
        ),
      }))}
    />
  );
}
