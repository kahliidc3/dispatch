import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { DomainsTable } from "@/app/(dashboard)/domains/_components/domains-table";
import { DnsRecords } from "@/app/(dashboard)/domains/_components/dns-records";
import type { DnsRecord, DomainListItem } from "@/types/domain";

const mockDomains: DomainListItem[] = [
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

const mockDnsRecords: DnsRecord[] = [
  {
    id: "rec-spf",
    type: "TXT",
    hostname: "m47.dispatch.internal",
    value: "v=spf1 include:amazonses.com ~all",
    purpose: "spf",
    status: "pending",
    lastCheckedAt: null,
  },
  {
    id: "rec-dkim",
    type: "CNAME",
    hostname: "dkimsel1._domainkey.m47.dispatch.internal",
    value: "dkimsel1.dkim.amazonses.com",
    purpose: "dkim",
    status: "valid",
    lastCheckedAt: "2026-04-22T14:00:00Z",
  },
  {
    id: "rec-dmarc",
    type: "TXT",
    hostname: "_dmarc.m47.dispatch.internal",
    value: "v=DMARC1; p=quarantine; rua=mailto:dmarc@dispatch.internal",
    purpose: "dmarc",
    status: "invalid",
    lastCheckedAt: "2026-04-22T14:00:00Z",
  },
];

describe("DomainsTable", () => {
  it("renders domain rows with correct status badges", () => {
    render(<DomainsTable initialDomains={mockDomains} />);

    expect(screen.getByText("m47.dispatch.internal")).toBeInTheDocument();
    expect(screen.getByText("m48.dispatch.internal")).toBeInTheDocument();
    expect(screen.getByText("m49.dispatch.internal")).toBeInTheDocument();

    expect(screen.getByText("pending")).toBeInTheDocument();
    expect(screen.getByText("verified")).toBeInTheDocument();
    expect(screen.getByText("verifying")).toBeInTheDocument();
  });

  it("links each domain name to its detail page", () => {
    render(<DomainsTable initialDomains={mockDomains} />);

    expect(screen.getByRole("link", { name: "m47.dispatch.internal" })).toHaveAttribute(
      "href",
      "/domains/dom-001",
    );
    expect(screen.getByRole("link", { name: "m48.dispatch.internal" })).toHaveAttribute(
      "href",
      "/domains/dom-002",
    );
  });

  it("shows empty state when no domains are provided", () => {
    render(<DomainsTable initialDomains={[]} />);

    expect(screen.getByText("No domains yet")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Add domain" }),
    ).toBeInTheDocument();
  });
});

describe("DnsRecords", () => {
  it("renders all records with purpose labels and status badges", () => {
    render(<DnsRecords records={mockDnsRecords} />);

    expect(screen.getByText("SPF")).toBeInTheDocument();
    expect(screen.getByText("DKIM")).toBeInTheDocument();
    expect(screen.getByText("DMARC")).toBeInTheDocument();
  });

  it("shows correct status badges per record", () => {
    render(<DnsRecords records={mockDnsRecords} />);

    expect(screen.getByText("pending")).toBeInTheDocument();
    expect(screen.getByText("valid")).toBeInTheDocument();
    expect(screen.getByText("invalid")).toBeInTheDocument();
  });

  it("renders record hostnames and values", () => {
    render(<DnsRecords records={mockDnsRecords} />);

    expect(screen.getByText("m47.dispatch.internal")).toBeInTheDocument();
    expect(screen.getByText("v=spf1 include:amazonses.com ~all")).toBeInTheDocument();
    expect(
      screen.getByText("dkimsel1._domainkey.m47.dispatch.internal"),
    ).toBeInTheDocument();
  });

  it("renders copy buttons for each record", () => {
    render(<DnsRecords records={mockDnsRecords} />);

    const copyButtons = screen.getAllByRole("button", { name: /copy/i });
    expect(copyButtons.length).toBeGreaterThanOrEqual(mockDnsRecords.length);
  });

  it("renders a copy-all button", () => {
    render(<DnsRecords records={mockDnsRecords} />);

    expect(
      screen.getByRole("button", { name: /copy all/i }),
    ).toBeInTheDocument();
  });

  it("shows not-yet-checked label when lastCheckedAt is null", () => {
    render(<DnsRecords records={mockDnsRecords} />);

    expect(screen.getByText("Not yet checked")).toBeInTheDocument();
  });
});
