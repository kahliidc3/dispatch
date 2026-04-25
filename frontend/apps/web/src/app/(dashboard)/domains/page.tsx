import Link from "next/link";
import { Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { PageIntro } from "@/components/patterns/page-intro";
import { domainList } from "./_lib/domains-queries";
import { DomainsTable } from "./_components/domains-table";

export default function DomainsPage() {
  return (
    <div className="page-stack">
      <PageIntro
        title="Domains"
        description="Add sending domains, set up DNS records, verify ownership, and manage domain lifecycle."
        actions={
          <Button asChild>
            <Link href="/domains/new">
              <Plus className="h-4 w-4" aria-hidden />
              Add domain
            </Link>
          </Button>
        }
      />
      <DomainsTable initialDomains={domainList} />
    </div>
  );
}
