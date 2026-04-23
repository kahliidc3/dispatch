import { DataTable } from "@/components/shared/data-table";
import { Badge } from "@/components/ui/badge";

const apiKeys = [
  {
    name: "Import worker",
    prefix: "disp_12ab",
    lastUsed: "2026-04-23 09:10",
    status: "active",
  },
  {
    name: "Ops audit",
    prefix: "disp_54cd",
    lastUsed: "2026-04-22 19:45",
    status: "revoked",
  },
];

export default function SettingsApiKeysPage() {
  return (
    <div className="page-stack">
      <header className="page-header">
        <div>
          <h1 className="page-title">API keys</h1>
          <p className="page-description">
            Key creation, one-time reveal, and revocation workflows land in
            Sprint 02. This route locks the future screen path now.
          </p>
        </div>
      </header>
      <DataTable
        caption="Static API key placeholder"
        columns={[
          { key: "name", label: "Name" },
          { key: "prefix", label: "Prefix", className: "mono text-xs" },
          { key: "lastUsed", label: "Last used" },
          { key: "status", label: "Status" },
        ]}
        rows={apiKeys.map((key) => ({
          name: key.name,
          prefix: key.prefix,
          lastUsed: key.lastUsed,
          status: (
            <Badge variant={key.status === "active" ? "success" : "outline"}>
              {key.status}
            </Badge>
          ),
        }))}
      />
    </div>
  );
}
