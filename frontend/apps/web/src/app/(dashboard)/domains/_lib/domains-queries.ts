import type { DomainRecord } from "@/types/domain";

export const domains: DomainRecord[] = [
  {
    id: "dom-001",
    name: "m47.dispatch.internal",
    verification: "pending",
    reputation: "warming",
    breaker: "closed",
    updatedAt: "2026-04-23T08:05:00Z",
  },
  {
    id: "dom-002",
    name: "m48.dispatch.internal",
    verification: "verified",
    reputation: "healthy",
    breaker: "closed",
    updatedAt: "2026-04-23T09:45:00Z",
  },
  {
    id: "dom-003",
    name: "m49.dispatch.internal",
    verification: "verifying",
    reputation: "cooling",
    breaker: "open",
    updatedAt: "2026-04-23T10:55:00Z",
  },
];

export function getDomainById(domainId: string) {
  return domains.find((domain) => domain.id === domainId) ?? domains[0];
}
