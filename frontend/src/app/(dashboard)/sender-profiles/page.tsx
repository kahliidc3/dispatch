import { PageIntro } from "@/components/patterns/page-intro";
import { getVerifiedDomains } from "../domains/_lib/domains-queries";
import { senderProfiles } from "./_lib/sender-profiles-queries";
import { SenderProfilesManager } from "./_components/sender-profiles-manager";

export default function SenderProfilesPage() {
  const verifiedDomains = getVerifiedDomains();

  return (
    <div className="page-stack">
      <PageIntro
        title="Sender profiles"
        description="Define the from addresses and display names used in outgoing campaigns. Only verified domains may be used."
      />
      <SenderProfilesManager
        initialProfiles={senderProfiles}
        verifiedDomains={verifiedDomains}
      />
    </div>
  );
}
