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

export type ProvisioningProvider = "manual" | "cloudflare" | "route53";
export type ProvisioningStepStatus =
  | "pending"
  | "running"
  | "success"
  | "failed"
  | "skipped";
export type ProvisioningStatus =
  | "in_progress"
  | "completed"
  | "failed"
  | "abandoned";

export type ProvisioningStep = {
  key: string;
  label: string;
  status: ProvisioningStepStatus;
  startedAt: string | null;
  completedAt: string | null;
  elapsedMs: number | null;
  errorDetail: string | null;
};

export type ProvisioningAttempt = {
  id: string;
  domainId: string;
  domainName: string;
  provider: ProvisioningProvider;
  status: ProvisioningStatus;
  steps: ProvisioningStep[];
  startedAt: string;
  completedAt: string | null;
  failureReason: string | null;
  failureRemediation: string | null;
};

export type DnsZone = {
  id: string;
  name: string;
  provider: Exclude<ProvisioningProvider, "manual">;
};

export type ThrottleStatus = {
  domainId: string;
  rateLimit: number;
  tokensAvailable: number;
  refillRate: number;
  denialsPerMinute: number;
  updatedAt: string;
};

export type DenialEvent = {
  id: string;
  domainId: string;
  occurredAt: string;
  reason: string;
  recipientCount: number;
};

export type WarmupPreset = "conservative" | "standard" | "aggressive" | "custom";
export type WarmupLifecycle = "warming" | "healthy" | "cooling" | "burnt" | "retired";

export type WarmupDay = {
  day: number;
  cap: number;
  actualSends: number | null;
};

export type WarmupSchedule = {
  preset: WarmupPreset;
  totalDays: number;
  days: WarmupDay[];
};

export type WarmupStatus = {
  domainId: string;
  lifecycle: WarmupLifecycle;
  currentDay: number;
  totalDays: number;
  todayCap: number;
  todaySends: number;
  scheduledGraduationAt: string | null;
  graduatedAt: string | null;
  schedule: WarmupSchedule;
};

export type PostmasterReputation = "high" | "medium" | "low" | "bad";

export type PostmasterDayMetric = {
  date: string;
  spamRatePct: number;
  domainReputation: PostmasterReputation;
  spfPassPct: number;
  dkimPassPct: number;
  dmarcPassPct: number;
};

export type PostmasterData = {
  domainId: string;
  connected: boolean;
  asOf: string | null;
  metrics: PostmasterDayMetric[];
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
