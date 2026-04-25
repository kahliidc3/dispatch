import { PageIntro } from "@/components/patterns/page-intro";
import { requireAdmin } from "@/lib/auth/guards";
import { UsersManager } from "./_components/users-manager";

const initialUsers = [
  {
    id: "user-ops-admin",
    name: "Ops Admin",
    email: "ops-admin@dispatch.internal",
    role: "admin",
    status: "active",
    lastLoginAt: "2026-04-23T11:20:00.000Z",
    mfaState: "enrolled",
  },
  {
    id: "user-campaign-operator",
    name: "Campaign Operator",
    email: "campaign-operator@dispatch.internal",
    role: "user",
    status: "active",
    lastLoginAt: "2026-04-22T17:40:00.000Z",
    mfaState: "enrolled",
  },
  {
    id: "user-qa-shadow",
    name: "QA Shadow",
    email: "qa-shadow@dispatch.internal",
    role: "user",
    status: "disabled",
    lastLoginAt: null,
    mfaState: "reset_required",
  },
] as const;

export default async function SettingsUsersPage() {
  await requireAdmin();

  return (
    <div className="page-stack">
      <PageIntro
        title="Users"
        description="Admin-only controls for creating operators, suspending access, and forcing MFA reset without exposing secret material in the browser."
      />
      <UsersManager initialUsers={[...initialUsers]} />
    </div>
  );
}
