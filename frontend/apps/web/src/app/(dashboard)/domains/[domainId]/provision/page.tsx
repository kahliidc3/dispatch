import Link from "next/link";
import { notFound } from "next/navigation";
import { Badge } from "@/components/ui/badge";
import { getDomainDetail } from "../../_lib/domains-queries";
import { getMockProvisioningAttempt } from "../../_lib/provisioning-queries";
import { StepLog } from "./_components/step-log";

const providerLabel: Record<string, string> = {
  manual: "Manual",
  cloudflare: "Cloudflare",
  route53: "Route 53",
};

type Props = { params: Promise<{ domainId: string }> };

export default async function ProvisionPage({ params }: Props) {
  const { domainId } = await params;
  const domain = getDomainDetail(domainId);
  if (!domain) notFound();

  const attempt = getMockProvisioningAttempt(domainId);

  return (
    <div className="page-stack">
      <header className="page-header">
        <div>
          <p className="text-sm text-text-muted">
            <Link href="/domains" className="hover:underline">
              Domains
            </Link>{" "}
            /{" "}
            <Link href={`/domains/${domainId}`} className="hover:underline">
              {domain.name}
            </Link>{" "}
            / Provisioning
          </p>
          <h1 className="page-title">Provisioning</h1>
        </div>
        {attempt && (
          <div className="page-actions">
            <Badge variant="outline">
              {providerLabel[attempt.provider] ?? attempt.provider}
            </Badge>
          </div>
        )}
      </header>

      {attempt ? (
        <StepLog initialAttempt={attempt} domainId={domainId} />
      ) : (
        <div className="surface-panel p-6">
          <p className="text-sm text-text-muted">
            No provisioning attempt found for this domain.{" "}
            <Link href={`/domains/${domainId}`} className="hover:underline">
              Return to domain detail.
            </Link>
          </p>
        </div>
      )}
    </div>
  );
}
