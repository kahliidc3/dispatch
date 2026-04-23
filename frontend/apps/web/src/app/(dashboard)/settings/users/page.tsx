import { DataTable } from "@/components/shared/data-table";
import { Badge } from "@/components/ui/badge";

const users = [
  { name: "Ops Admin", role: "admin", status: "active" },
  { name: "Campaign Operator", role: "user", status: "active" },
];

export default function SettingsUsersPage() {
  return (
    <div className="page-stack">
      <header className="page-header">
        <div>
          <h1 className="page-title">Users</h1>
          <p className="page-description">
            User creation, role edits, and MFA resets land in Sprint 02. This
            page keeps the nested settings route stable.
          </p>
        </div>
      </header>
      <DataTable
        caption="Static user list placeholder"
        columns={[
          { key: "name", label: "Name" },
          { key: "role", label: "Role" },
          { key: "status", label: "Status" },
        ]}
        rows={users.map((user) => ({
          name: user.name,
          role: user.role,
          status: <Badge variant="success">{user.status}</Badge>,
        }))}
      />
    </div>
  );
}
