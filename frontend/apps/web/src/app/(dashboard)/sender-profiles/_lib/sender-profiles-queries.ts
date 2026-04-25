import type { SenderProfile } from "@/types/domain";

export const senderProfiles: SenderProfile[] = [
  {
    id: "sp-001",
    name: "Campaign broadcast",
    fromName: "Dispatch Platform",
    fromEmail: "noreply@m48.dispatch.internal",
    replyTo: null,
    domainId: "dom-002",
    domainName: "m48.dispatch.internal",
    ipPool: "shared-pool-us-east",
    status: "active",
    createdAt: "2026-04-11T09:00:00Z",
    updatedAt: "2026-04-23T09:45:00Z",
  },
  {
    id: "sp-002",
    name: "Transactional alerts",
    fromName: "Dispatch Alerts",
    fromEmail: "alerts@m48.dispatch.internal",
    replyTo: "support@dispatch.internal",
    domainId: "dom-002",
    domainName: "m48.dispatch.internal",
    ipPool: "dedicated-pool-us-east-01",
    status: "active",
    createdAt: "2026-04-14T13:30:00Z",
    updatedAt: "2026-04-22T16:20:00Z",
  },
];

export function getSenderProfileById(id: string): SenderProfile | undefined {
  return senderProfiles.find((p) => p.id === id);
}
