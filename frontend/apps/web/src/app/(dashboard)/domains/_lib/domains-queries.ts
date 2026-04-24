import type { DnsRecord, DomainDetail, DomainListItem } from "@/types/domain";

const dnsRecordsPending: DnsRecord[] = [
  {
    id: "rec-001-spf",
    type: "TXT",
    hostname: "m47.dispatch.internal",
    value: "v=spf1 include:amazonses.com ~all",
    purpose: "spf",
    status: "pending",
    lastCheckedAt: null,
  },
  {
    id: "rec-001-dkim1",
    type: "CNAME",
    hostname: "dkimsel1._domainkey.m47.dispatch.internal",
    value: "dkimsel1.dkim.amazonses.com",
    purpose: "dkim",
    status: "pending",
    lastCheckedAt: null,
  },
  {
    id: "rec-001-dkim2",
    type: "CNAME",
    hostname: "dkimsel2._domainkey.m47.dispatch.internal",
    value: "dkimsel2.dkim.amazonses.com",
    purpose: "dkim",
    status: "pending",
    lastCheckedAt: null,
  },
  {
    id: "rec-001-dmarc",
    type: "TXT",
    hostname: "_dmarc.m47.dispatch.internal",
    value: "v=DMARC1; p=quarantine; rua=mailto:dmarc@dispatch.internal",
    purpose: "dmarc",
    status: "pending",
    lastCheckedAt: null,
  },
  {
    id: "rec-001-mailfrom",
    type: "MX",
    hostname: "mail.m47.dispatch.internal",
    value: "10 feedback-smtp.us-east-1.amazonses.com",
    purpose: "mail_from",
    status: "pending",
    lastCheckedAt: null,
  },
];

const dnsRecordsValid: DnsRecord[] = [
  {
    id: "rec-002-spf",
    type: "TXT",
    hostname: "m48.dispatch.internal",
    value: "v=spf1 include:amazonses.com ~all",
    purpose: "spf",
    status: "valid",
    lastCheckedAt: "2026-04-22T14:00:00Z",
  },
  {
    id: "rec-002-dkim1",
    type: "CNAME",
    hostname: "dkimsel1._domainkey.m48.dispatch.internal",
    value: "dkimsel1.dkim.amazonses.com",
    purpose: "dkim",
    status: "valid",
    lastCheckedAt: "2026-04-22T14:00:00Z",
  },
  {
    id: "rec-002-dkim2",
    type: "CNAME",
    hostname: "dkimsel2._domainkey.m48.dispatch.internal",
    value: "dkimsel2.dkim.amazonses.com",
    purpose: "dkim",
    status: "valid",
    lastCheckedAt: "2026-04-22T14:00:00Z",
  },
  {
    id: "rec-002-dmarc",
    type: "TXT",
    hostname: "_dmarc.m48.dispatch.internal",
    value: "v=DMARC1; p=quarantine; rua=mailto:dmarc@dispatch.internal",
    purpose: "dmarc",
    status: "valid",
    lastCheckedAt: "2026-04-22T14:00:00Z",
  },
  {
    id: "rec-002-mailfrom",
    type: "MX",
    hostname: "mail.m48.dispatch.internal",
    value: "10 feedback-smtp.us-east-1.amazonses.com",
    purpose: "mail_from",
    status: "valid",
    lastCheckedAt: "2026-04-22T14:00:00Z",
  },
];

const dnsRecordsMixed: DnsRecord[] = [
  {
    id: "rec-003-spf",
    type: "TXT",
    hostname: "m49.dispatch.internal",
    value: "v=spf1 include:amazonses.com ~all",
    purpose: "spf",
    status: "valid",
    lastCheckedAt: "2026-04-23T10:30:00Z",
  },
  {
    id: "rec-003-dkim1",
    type: "CNAME",
    hostname: "dkimsel1._domainkey.m49.dispatch.internal",
    value: "dkimsel1.dkim.amazonses.com",
    purpose: "dkim",
    status: "invalid",
    lastCheckedAt: "2026-04-23T10:30:00Z",
  },
  {
    id: "rec-003-dkim2",
    type: "CNAME",
    hostname: "dkimsel2._domainkey.m49.dispatch.internal",
    value: "dkimsel2.dkim.amazonses.com",
    purpose: "dkim",
    status: "invalid",
    lastCheckedAt: "2026-04-23T10:30:00Z",
  },
  {
    id: "rec-003-dmarc",
    type: "TXT",
    hostname: "_dmarc.m49.dispatch.internal",
    value: "v=DMARC1; p=quarantine; rua=mailto:dmarc@dispatch.internal",
    purpose: "dmarc",
    status: "pending",
    lastCheckedAt: null,
  },
  {
    id: "rec-003-mailfrom",
    type: "MX",
    hostname: "mail.m49.dispatch.internal",
    value: "10 feedback-smtp.us-east-1.amazonses.com",
    purpose: "mail_from",
    status: "pending",
    lastCheckedAt: null,
  },
];

const domainDetails: Record<string, DomainDetail> = {
  "dom-001": {
    id: "dom-001",
    name: "m47.dispatch.internal",
    status: "pending",
    breaker: "closed",
    createdAt: "2026-04-20T08:00:00Z",
    updatedAt: "2026-04-23T08:05:00Z",
    dnsRecords: dnsRecordsPending,
  },
  "dom-002": {
    id: "dom-002",
    name: "m48.dispatch.internal",
    status: "verified",
    breaker: "closed",
    createdAt: "2026-04-10T11:00:00Z",
    updatedAt: "2026-04-23T09:45:00Z",
    dnsRecords: dnsRecordsValid,
  },
  "dom-003": {
    id: "dom-003",
    name: "m49.dispatch.internal",
    status: "verifying",
    breaker: "open",
    createdAt: "2026-04-21T15:00:00Z",
    updatedAt: "2026-04-23T10:55:00Z",
    dnsRecords: dnsRecordsMixed,
  },
};

export const domainList: DomainListItem[] = [
  {
    id: "dom-001",
    name: "m47.dispatch.internal",
    status: "pending",
    breaker: "closed",
    updatedAt: "2026-04-23T08:05:00Z",
  },
  {
    id: "dom-002",
    name: "m48.dispatch.internal",
    status: "verified",
    breaker: "closed",
    updatedAt: "2026-04-23T09:45:00Z",
  },
  {
    id: "dom-003",
    name: "m49.dispatch.internal",
    status: "verifying",
    breaker: "open",
    updatedAt: "2026-04-23T10:55:00Z",
  },
];

export function getDomainDetail(id: string): DomainDetail | undefined {
  return domainDetails[id];
}

export function getVerifiedDomains(): DomainListItem[] {
  return domainList.filter((d) => d.status === "verified");
}
