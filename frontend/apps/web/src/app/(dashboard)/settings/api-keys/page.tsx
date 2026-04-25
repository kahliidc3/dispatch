import { PageIntro } from "@/components/patterns/page-intro";
import { requireAdmin } from "@/lib/auth/guards";
import { ApiKeysManager } from "./_components/api-keys-manager";

const initialApiKeys = [
  {
    id: "key-import-worker",
    name: "Import worker",
    prefix: "ak_live_opr921",
    last4: "M9qZ",
    createdAt: "2026-04-18T08:25:00.000Z",
    lastUsedAt: "2026-04-23T09:10:00.000Z",
    revokedAt: null,
    status: "active",
  },
  {
    id: "key-ops-audit",
    name: "Ops audit",
    prefix: "ak_live_ztm114",
    last4: "D3fL",
    createdAt: "2026-04-09T16:45:00.000Z",
    lastUsedAt: "2026-04-22T19:45:00.000Z",
    revokedAt: "2026-04-23T18:05:00.000Z",
    status: "revoked",
    revokedReason: "Rotated after quarterly credential review",
  },
] as const;

export default async function SettingsApiKeysPage() {
  await requireAdmin();

  return (
    <div className="page-stack">
      <PageIntro
        title="API keys"
        description="Manage internal integration credentials with one-time secret reveal, explicit revocation reasons, and a table that only shows safe metadata."
      />
      <ApiKeysManager initialKeys={[...initialApiKeys]} />
    </div>
  );
}
