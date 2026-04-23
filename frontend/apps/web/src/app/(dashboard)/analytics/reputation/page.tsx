import { Badge } from "@/components/ui/badge";
import { DataTable } from "@/components/shared/data-table";
import { domains } from "../../domains/_lib/domains-queries";

const reputationVariant = {
  warming: "warning",
  healthy: "success",
  cooling: "outline",
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
        caption="Static reputation placeholder"
        columns={[
          { key: "domain", label: "Domain" },
          { key: "verification", label: "Verification" },
          { key: "reputation", label: "Reputation" },
          { key: "breaker", label: "Breaker" },
        ]}
        rows={domains.map((domain) => ({
          domain: domain.name,
          verification: domain.verification,
          reputation: (
            <Badge variant={reputationVariant[domain.reputation]}>
              {domain.reputation}
            </Badge>
          ),
          breaker: domain.breaker,
        }))}
      />
    </div>
  );
}
