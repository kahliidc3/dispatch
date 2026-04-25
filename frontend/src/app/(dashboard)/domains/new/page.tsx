import Link from "next/link";
import { ProvisioningWizard } from "./_components/provisioning-wizard";

export default function NewDomainPage() {
  return (
    <div className="page-stack">
      <header className="page-header">
        <div>
          <p className="text-sm text-text-muted">
            <Link href="/domains" className="hover:underline">
              Domains
            </Link>{" "}
            / Add domain
          </p>
          <h1 className="page-title">Add domain</h1>
        </div>
      </header>

      <ProvisioningWizard />
    </div>
  );
}
