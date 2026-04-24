import { PageIntro } from "@/components/patterns/page-intro";
import { domainList } from "./_lib/domains-queries";
import { AddDomainDialog } from "./_components/add-domain-dialog";
import { DomainsTable } from "./_components/domains-table";

export default function DomainsPage() {
  return (
    <div className="page-stack">
      <PageIntro
        title="Domains"
        description="Add sending domains, set up DNS records, verify ownership, and manage domain lifecycle."
        actions={<AddDomainDialog />}
      />
      <DomainsTable initialDomains={domainList} />
    </div>
  );
}
