export type DomainStatus =
  | "pending"
  | "verifying"
  | "verified"
  | "cooling"
  | "burnt"
  | "retired";

export type DnsRecordStatus = "pending" | "valid" | "invalid";
export type DnsRecordType = "TXT" | "CNAME" | "MX";
export type BreakerState = "closed" | "open";

export type DnsRecord = {
  id: string;
  type: DnsRecordType;
  hostname: string;
  value: string;
  purpose: "spf" | "dkim" | "dmarc" | "mail_from";
  status: DnsRecordStatus;
  lastCheckedAt: string | null;
};

export type DomainListItem = {
  id: string;
  name: string;
  status: DomainStatus;
  breaker: BreakerState;
  updatedAt: string;
};

export type DomainDetail = {
  id: string;
  name: string;
  status: DomainStatus;
  breaker: BreakerState;
  createdAt: string;
  updatedAt: string;
  dnsRecords: DnsRecord[];
};

export type SenderProfileStatus = "active" | "suspended";

export type SenderProfile = {
  id: string;
  name: string;
  fromName: string;
  fromEmail: string;
  replyTo: string | null;
  domainId: string;
  domainName: string;
  ipPool: string | null;
  status: SenderProfileStatus;
  createdAt: string;
  updatedAt: string;
};
