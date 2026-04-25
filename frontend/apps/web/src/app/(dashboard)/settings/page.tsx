import Link from "next/link";
import { EmptyState } from "@/components/shared/empty-state";

export default function SettingsPage() {
  return (
    <div className="page-stack">
      <header className="page-header">
        <div>
          <h1 className="page-title">Settings</h1>
          <p className="page-description">
            Settings subsections are scaffolded for users and API keys. Security
            and audit surfaces arrive in later sprints.
          </p>
        </div>
      </header>
      <section className="surface-panel p-6">
        <div className="grid gap-3">
          <Link href="/settings/users" className="rail-link">
            Users
          </Link>
          <Link href="/settings/api-keys" className="rail-link">
            API keys
          </Link>
        </div>
      </section>
      <EmptyState
        title="Settings placeholder"
        description="This index route exists so later settings surfaces can be added without changing the shell."
      />
    </div>
  );
}
