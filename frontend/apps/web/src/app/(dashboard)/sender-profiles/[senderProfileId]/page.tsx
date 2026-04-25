import Link from "next/link";
import { notFound } from "next/navigation";
import { Badge } from "@/components/ui/badge";
import { SectionPanel } from "@/components/patterns/section-panel";
import { formatTimestamp } from "@/lib/formatters";
import { CircuitBreakerBadge } from "@/components/shared/circuit-breaker-badge";
import { getBreakerForEntity } from "@/app/(dashboard)/ops/_lib/ops-queries";
import { getSenderProfileById } from "../_lib/sender-profiles-queries";

type SenderProfileDetailPageProps = {
  params: Promise<{ senderProfileId: string }>;
};

export default async function SenderProfileDetailPage({
  params,
}: SenderProfileDetailPageProps) {
  const { senderProfileId } = await params;
  const profile = getSenderProfileById(senderProfileId);

  if (!profile) notFound();

  const breaker = getBreakerForEntity("sender_profile", profile.id);

  return (
    <div className="page-stack">
      <header className="page-header">
        <div>
          <p className="text-sm text-text-muted">
            <Link href="/sender-profiles" className="hover:underline">
              Sender profiles
            </Link>{" "}
            / {profile.name}
          </p>
          <h1 className="page-title">{profile.name}</h1>
        </div>
      </header>

      <SectionPanel title="Profile details">
        <div className="summary-list">
          <div className="summary-row">
            <span className="text-sm font-medium">Status</span>
            <Badge variant={profile.status === "active" ? "success" : "outline"}>
              {profile.status}
            </Badge>
          </div>
          <div className="summary-row">
            <span className="text-sm font-medium">Display name</span>
            <span className="text-sm">{profile.fromName}</span>
          </div>
          <div className="summary-row">
            <span className="text-sm font-medium">From address</span>
            <span className="text-sm font-mono">{profile.fromEmail}</span>
          </div>
          <div className="summary-row">
            <span className="text-sm font-medium">Reply-To</span>
            <span className="text-sm text-text-muted">
              {profile.replyTo ?? "Not set"}
            </span>
          </div>
          <div className="summary-row">
            <span className="text-sm font-medium">Sending domain</span>
            <Link
              href={`/domains/${profile.domainId}`}
              className="text-sm hover:underline"
            >
              {profile.domainName}
            </Link>
          </div>
          {breaker && (
            <div className="summary-row">
              <span className="text-sm font-medium">Circuit breaker</span>
              <CircuitBreakerBadge
                scope="sender_profile"
                entityId={profile.id}
                state={breaker.state}
              />
            </div>
          )}
          <div className="summary-row">
            <span className="text-sm font-medium">Created</span>
            <span className="text-sm text-text-muted">
              {formatTimestamp(profile.createdAt)}
            </span>
          </div>
          <div className="summary-row">
            <span className="text-sm font-medium">Last updated</span>
            <span className="text-sm text-text-muted">
              {formatTimestamp(profile.updatedAt)}
            </span>
          </div>
        </div>
      </SectionPanel>

      <SectionPanel title="IP pool assignment">
        <div className="summary-list">
          <div className="summary-row">
            <span className="text-sm font-medium">Assigned pool</span>
            <span className="text-sm text-text-muted">
              {profile.ipPool ?? "Default shared pool"}
            </span>
          </div>
        </div>
        <p className="text-sm text-text-muted">
          IP pool assignment is managed by platform admins. Contact an admin to
          change the pool for this profile.
        </p>
      </SectionPanel>
    </div>
  );
}
