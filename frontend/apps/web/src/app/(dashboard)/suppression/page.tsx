import { getSession } from "@/lib/auth/session";
import { isAdmin } from "@/lib/auth/guards";
import { SuppressionManager } from "./_components/suppression-manager";
import {
  mockSuppressionList,
  mockSyncStatus,
} from "./_lib/suppression-queries";

export default async function SuppressionPage() {
  const session = await getSession();
  const adminUser = isAdmin(session);

  return (
    <div className="page-stack">
      <header className="page-intro">
        <div className="page-intro-copy">
          <h1 className="page-title">Suppression list</h1>
          <p className="page-description">
            Platform-wide suppression entries. Emails here are excluded from all
            campaign sends. Removals are audited and require justification.
          </p>
        </div>
      </header>

      <SuppressionManager
        initialEntries={mockSuppressionList}
        syncStatus={mockSyncStatus}
        isAdmin={adminUser}
      />
    </div>
  );
}
