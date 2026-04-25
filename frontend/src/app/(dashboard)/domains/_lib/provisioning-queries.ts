import type {
  DnsZone,
  ProvisioningAttempt,
  ProvisioningProvider,
  ProvisioningStep,
} from "@/types/domain";

const mockZones: DnsZone[] = [
  { id: "zone-cf-001", name: "dispatch.internal", provider: "cloudflare" },
  { id: "zone-cf-002", name: "internal.dispatch.io", provider: "cloudflare" },
  { id: "zone-r53-001", name: "dispatch.internal", provider: "route53" },
  { id: "zone-r53-002", name: "aws.dispatch.internal", provider: "route53" },
];

export function getMockZones(
  provider: Exclude<ProvisioningProvider, "manual">,
): DnsZone[] {
  return mockZones.filter((z) => z.provider === provider);
}

const STEPS_COMPLETED: ProvisioningStep[] = [
  {
    key: "create_ses",
    label: "Create SES identity",
    status: "success",
    startedAt: "2026-04-24T08:30:00Z",
    completedAt: "2026-04-24T08:30:02Z",
    elapsedMs: 2300,
    errorDetail: null,
  },
  {
    key: "fetch_dkim",
    label: "Fetch DKIM tokens",
    status: "success",
    startedAt: "2026-04-24T08:30:02Z",
    completedAt: "2026-04-24T08:30:04Z",
    elapsedMs: 1100,
    errorDetail: null,
  },
  {
    key: "write_dns",
    label: "Write DNS records",
    status: "success",
    startedAt: "2026-04-24T08:30:04Z",
    completedAt: "2026-04-24T08:30:09Z",
    elapsedMs: 4800,
    errorDetail: null,
  },
  {
    key: "verify_ses",
    label: "Verify SES identity",
    status: "success",
    startedAt: "2026-04-24T08:30:09Z",
    completedAt: "2026-04-24T08:30:54Z",
    elapsedMs: 45200,
    errorDetail: null,
  },
  {
    key: "verify_dkim",
    label: "Verify DKIM",
    status: "success",
    startedAt: "2026-04-24T08:30:54Z",
    completedAt: "2026-04-24T08:31:56Z",
    elapsedMs: 62400,
    errorDetail: null,
  },
];

const STEPS_FAILED: ProvisioningStep[] = [
  {
    key: "create_ses",
    label: "Create SES identity",
    status: "success",
    startedAt: "2026-04-22T14:10:00Z",
    completedAt: "2026-04-22T14:10:02Z",
    elapsedMs: 2100,
    errorDetail: null,
  },
  {
    key: "fetch_dkim",
    label: "Fetch DKIM tokens",
    status: "success",
    startedAt: "2026-04-22T14:10:02Z",
    completedAt: "2026-04-22T14:10:04Z",
    elapsedMs: 900,
    errorDetail: null,
  },
  {
    key: "write_dns",
    label: "Write DNS records",
    status: "failed",
    startedAt: "2026-04-22T14:10:04Z",
    completedAt: "2026-04-22T14:10:06Z",
    elapsedMs: 1800,
    errorDetail:
      "Access denied to DNS zone 'dispatch.internal'. Verify the API token has Zone:Edit permission.",
  },
  {
    key: "verify_ses",
    label: "Verify SES identity",
    status: "skipped",
    startedAt: null,
    completedAt: null,
    elapsedMs: null,
    errorDetail: null,
  },
  {
    key: "verify_dkim",
    label: "Verify DKIM",
    status: "skipped",
    startedAt: null,
    completedAt: null,
    elapsedMs: null,
    errorDetail: null,
  },
];

const STEPS_IN_PROGRESS: ProvisioningStep[] = [
  {
    key: "create_ses",
    label: "Create SES identity",
    status: "success",
    startedAt: "2026-04-24T09:58:00Z",
    completedAt: "2026-04-24T09:58:02Z",
    elapsedMs: 2100,
    errorDetail: null,
  },
  {
    key: "fetch_dkim",
    label: "Fetch DKIM tokens",
    status: "success",
    startedAt: "2026-04-24T09:58:02Z",
    completedAt: "2026-04-24T09:58:03Z",
    elapsedMs: 800,
    errorDetail: null,
  },
  {
    key: "write_dns",
    label: "Write DNS records",
    status: "success",
    startedAt: "2026-04-24T09:58:03Z",
    completedAt: "2026-04-24T09:58:08Z",
    elapsedMs: 4500,
    errorDetail: null,
  },
  {
    key: "verify_ses",
    label: "Verify SES identity",
    status: "running",
    startedAt: "2026-04-24T09:58:08Z",
    completedAt: null,
    elapsedMs: null,
    errorDetail: null,
  },
  {
    key: "verify_dkim",
    label: "Verify DKIM",
    status: "pending",
    startedAt: null,
    completedAt: null,
    elapsedMs: null,
    errorDetail: null,
  },
];

const provisioningAttempts: ProvisioningAttempt[] = [
  {
    id: "prov-001",
    domainId: "dom-003",
    domainName: "m49.dispatch.internal",
    provider: "cloudflare",
    status: "completed",
    steps: STEPS_COMPLETED,
    startedAt: "2026-04-24T08:30:00Z",
    completedAt: "2026-04-24T08:31:56Z",
    failureReason: null,
    failureRemediation: null,
  },
  {
    id: "prov-002",
    domainId: "dom-002",
    domainName: "m48.dispatch.internal",
    provider: "cloudflare",
    status: "completed",
    steps: STEPS_COMPLETED,
    startedAt: "2026-04-10T11:10:00Z",
    completedAt: "2026-04-10T11:11:56Z",
    failureReason: null,
    failureRemediation: null,
  },
  {
    id: "prov-003",
    domainId: "dom-001",
    domainName: "m47.dispatch.internal",
    provider: "manual",
    status: "completed",
    steps: [],
    startedAt: "2026-04-20T08:00:00Z",
    completedAt: "2026-04-20T08:00:01Z",
    failureReason: null,
    failureRemediation: null,
  },
  {
    id: "prov-004",
    domainId: "dom-004",
    domainName: "m50.dispatch.internal",
    provider: "cloudflare",
    status: "failed",
    steps: STEPS_FAILED,
    startedAt: "2026-04-22T14:10:00Z",
    completedAt: "2026-04-22T14:10:06Z",
    failureReason: "dns_write_failed",
    failureRemediation:
      "Ensure the Cloudflare API token has Zone:Edit permission for the selected zone.",
  },
  {
    id: "prov-005",
    domainId: "dom-005",
    domainName: "m51.dispatch.internal",
    provider: "route53",
    status: "in_progress",
    steps: STEPS_IN_PROGRESS,
    startedAt: "2026-04-24T09:58:00Z",
    completedAt: null,
    failureReason: null,
    failureRemediation: null,
  },
];

export function getMockProvisioningAttempt(
  domainId: string,
): ProvisioningAttempt | null {
  return provisioningAttempts.find((a) => a.domainId === domainId) ?? null;
}

export function getMockProvisioningAudit(): ProvisioningAttempt[] {
  return provisioningAttempts;
}
