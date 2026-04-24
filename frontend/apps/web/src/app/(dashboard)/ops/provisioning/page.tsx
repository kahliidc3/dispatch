import { SectionPanel } from "@/components/patterns/section-panel";
import { getMockProvisioningAudit } from "@/app/(dashboard)/domains/_lib/provisioning-queries";
import { ProvisioningAudit } from "./_components/provisioning-audit";

export default function ProvisioningAuditPage() {
  const attempts = getMockProvisioningAudit();

  return (
    <div className="page-stack">
      <header className="page-header">
        <div>
          <h1 className="page-title">Provisioning</h1>
          <p className="page-description">
            Audit log for all automated domain provisioning attempts.
          </p>
        </div>
      </header>

      <SectionPanel>
        <ProvisioningAudit attempts={attempts} />
      </SectionPanel>
    </div>
  );
}
