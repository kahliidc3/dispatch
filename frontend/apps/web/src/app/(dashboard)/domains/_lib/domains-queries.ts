import type {
  DenialEvent,
  DnsRecord,
  DomainDetail,
  DomainListItem,
  ThrottleStatus,
} from "@/types/domain";

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

const throttleData: Record<string, ThrottleStatus> = {
  "dom-001": {
    domainId: "dom-001",
    rateLimit: 150,
    tokensAvailable: 142,
    refillRate: 2.5,
    denialsPerMinute: 0,
    updatedAt: "2026-04-24T09:55:00Z",
  },
  "dom-002": {
    domainId: "dom-002",
    rateLimit: 300,
    tokensAvailable: 81,
    refillRate: 5.0,
    denialsPerMinute: 3.2,
    updatedAt: "2026-04-24T09:57:00Z",
  },
  "dom-003": {
    domainId: "dom-003",
    rateLimit: 150,
    tokensAvailable: 0,
    refillRate: 2.5,
    denialsPerMinute: 14.7,
    updatedAt: "2026-04-24T09:58:00Z",
  },
};

export function getThrottleStatus(domainId: string): ThrottleStatus {
  return (
    throttleData[domainId] ?? {
      domainId,
      rateLimit: 150,
      tokensAvailable: 150,
      refillRate: 2.5,
      denialsPerMinute: 0,
      updatedAt: new Date().toISOString(),
    }
  );
}

const denialEventsData: Record<string, DenialEvent[]> = {
  "dom-002": [
    {
      id: "den-002-1",
      domainId: "dom-002",
      occurredAt: "2026-04-24T09:54:22Z",
      reason: "token_bucket_empty",
      recipientCount: 12,
    },
    {
      id: "den-002-2",
      domainId: "dom-002",
      occurredAt: "2026-04-24T09:50:07Z",
      reason: "token_bucket_empty",
      recipientCount: 8,
    },
    {
      id: "den-002-3",
      domainId: "dom-002",
      occurredAt: "2026-04-24T09:45:51Z",
      reason: "rate_limit_exceeded",
      recipientCount: 23,
    },
  ],
  "dom-003": [
    {
      id: "den-003-1",
      domainId: "dom-003",
      occurredAt: "2026-04-24T09:58:01Z",
      reason: "circuit_breaker_open",
      recipientCount: 150,
    },
    {
      id: "den-003-2",
      domainId: "dom-003",
      occurredAt: "2026-04-24T09:57:44Z",
      reason: "token_bucket_empty",
      recipientCount: 72,
    },
    {
      id: "den-003-3",
      domainId: "dom-003",
      occurredAt: "2026-04-24T09:55:30Z",
      reason: "token_bucket_empty",
      recipientCount: 91,
    },
    {
      id: "den-003-4",
      domainId: "dom-003",
      occurredAt: "2026-04-24T09:52:18Z",
      reason: "circuit_breaker_open",
      recipientCount: 88,
    },
    {
      id: "den-003-5",
      domainId: "dom-003",
      occurredAt: "2026-04-24T09:48:03Z",
      reason: "rate_limit_exceeded",
      recipientCount: 200,
    },
  ],
};

export function getDenialEvents(domainId: string): DenialEvent[] {
  return denialEventsData[domainId] ?? [];
}
