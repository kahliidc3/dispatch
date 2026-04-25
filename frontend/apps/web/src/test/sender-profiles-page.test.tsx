import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { SenderProfilesManager } from "@/app/(dashboard)/sender-profiles/_components/sender-profiles-manager";
import type { DomainListItem, SenderProfile } from "@/types/domain";

const mockVerifiedDomains: DomainListItem[] = [
  {
    id: "dom-002",
    name: "m48.dispatch.internal",
    status: "verified",
    breaker: "closed",
    updatedAt: "2026-04-23T09:45:00Z",
  },
];

const mockProfiles: SenderProfile[] = [
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
];

describe("SenderProfilesManager", () => {
  it("renders profiles with name and from address", () => {
    render(
      <SenderProfilesManager
        initialProfiles={mockProfiles}
        verifiedDomains={mockVerifiedDomains}
      />,
    );

    expect(screen.getByText("Campaign broadcast")).toBeInTheDocument();
    expect(screen.getByText("Dispatch Platform")).toBeInTheDocument();
    expect(screen.getByText(/noreply@m48\.dispatch\.internal/)).toBeInTheDocument();
  });

  it("links domain name to domain detail", () => {
    render(
      <SenderProfilesManager
        initialProfiles={mockProfiles}
        verifiedDomains={mockVerifiedDomains}
      />,
    );

    const domainLink = screen.getByRole("link", { name: "m48.dispatch.internal" });
    expect(domainLink).toHaveAttribute("href", "/domains/dom-002");
  });

  it("links profile name to profile detail", () => {
    render(
      <SenderProfilesManager
        initialProfiles={mockProfiles}
        verifiedDomains={mockVerifiedDomains}
      />,
    );

    const profileLink = screen.getByRole("link", { name: "Campaign broadcast" });
    expect(profileLink).toHaveAttribute("href", "/sender-profiles/sp-001");
  });

  it("shows create button when verified domains exist", () => {
    render(
      <SenderProfilesManager
        initialProfiles={[]}
        verifiedDomains={mockVerifiedDomains}
      />,
    );

    expect(
      screen.getByRole("button", { name: "Create profile" }),
    ).toBeEnabled();
  });

  it("disables create button when no verified domains exist", () => {
    render(
      <SenderProfilesManager
        initialProfiles={[]}
        verifiedDomains={[]}
      />,
    );

    expect(
      screen.getByRole("button", { name: "Create profile" }),
    ).toBeDisabled();
  });

  it("shows link to domains page when no verified domains exist", () => {
    render(
      <SenderProfilesManager
        initialProfiles={[]}
        verifiedDomains={[]}
      />,
    );

    expect(screen.getByRole("link", { name: "Add and verify a domain" })).toHaveAttribute(
      "href",
      "/domains",
    );
  });

  it("shows empty state when no profiles exist but domains are verified", () => {
    render(
      <SenderProfilesManager
        initialProfiles={[]}
        verifiedDomains={mockVerifiedDomains}
      />,
    );

    expect(screen.getByText("No sender profiles")).toBeInTheDocument();
  });

  it("shows a delete button per profile", () => {
    render(
      <SenderProfilesManager
        initialProfiles={mockProfiles}
        verifiedDomains={mockVerifiedDomains}
      />,
    );

    expect(
      screen.getByRole("button", { name: "Delete" }),
    ).toBeInTheDocument();
  });
});
