import { Badge } from "@/components/ui/badge";
import { DataTable } from "@/components/shared/data-table";
import { domainList } from "../../domains/_lib/domains-queries";

const statusVariant = {
  pending: "muted",
  verifying: "warning",
  verified: "success",
  cooling: "warning",
  burnt: "danger",
  retired: "outline",
} as const;

export default function ReputationPage() {
  return (
    <div className="page-stack">
      <header className="page-header">
        <div>
          <h1 className="page-title">Domain reputation</h1>
          <p className="page-description">
            This route reserves the domain health dashboard surface for the
            later analytics sprint.
          </p>
        </div>
      </header>
      <DataTable
        caption="Domain status overview"
        columns={[
          { key: "domain", label: "Domain" },
          { key: "status", label: "Status" },
          { key: "breaker", label: "Breaker" },
        ]}
        rows={domainList.map((domain) => ({
          domain: domain.name,
          status: (
            <Badge variant={statusVariant[domain.status]}>{domain.status}</Badge>
          ),
          breaker: domain.breaker,
        }))}
      />
    </div>
  );
}
