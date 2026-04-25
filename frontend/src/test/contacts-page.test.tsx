import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { ContactsTable } from "@/app/(dashboard)/contacts/_components/contacts-table";
import { ContactDrawer } from "@/app/(dashboard)/contacts/_components/contact-drawer";
import type { ContactListItem, ContactDetail } from "@/types/contact";
import type { List } from "@/types/list";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), refresh: vi.fn() }),
}));

vi.mock("sonner", () => ({ toast: { success: vi.fn(), error: vi.fn() } }));

vi.mock("@/lib/api/client", () => ({
  clientJson: vi.fn(),
}));

const mockContacts: ContactListItem[] = [
  {
    id: "ctc-001",
    email: "founder.alpha@example.com",
    firstName: "Alex",
    lastName: "Founder",
    lifecycle: "active",
    source: "csv_import",
    createdAt: "2026-03-15T09:00:00Z",
    updatedAt: "2026-04-23T07:20:00Z",
  },
  {
    id: "ctc-002",
    email: "ops.beta@example.com",
    firstName: "Blake",
    lastName: "Ops",
    lifecycle: "suppressed",
    source: "manual",
    createdAt: "2026-03-20T12:00:00Z",
    updatedAt: "2026-04-22T18:15:00Z",
  },
  {
    id: "ctc-003",
    email: "hello.gamma@example.com",
    firstName: null,
    lastName: null,
    lifecycle: "unsubscribed",
    source: "api",
    createdAt: "2026-04-01T08:00:00Z",
    updatedAt: "2026-04-21T11:40:00Z",
  },
];

const mockLists: List[] = [
  {
    id: "lst-001",
    name: "Early access",
    description: null,
    memberCount: 2,
    createdAt: "2026-04-01T10:00:00Z",
    updatedAt: "2026-04-23T08:00:00Z",
  },
];

describe("ContactsTable", () => {
  it("renders all contacts", () => {
    render(<ContactsTable contacts={mockContacts} lists={mockLists} />);
    expect(
      screen.getByText(/founder\.alpha@example\.com/),
    ).toBeInTheDocument();
    expect(screen.getByText(/ops\.beta@example\.com/)).toBeInTheDocument();
    expect(screen.getByText(/hello\.gamma@example\.com/)).toBeInTheDocument();
  });

  it("shows lifecycle badges", () => {
    render(<ContactsTable contacts={mockContacts} lists={mockLists} />);
    expect(screen.getByText("active")).toBeInTheDocument();
    expect(screen.getByText("suppressed")).toBeInTheDocument();
    expect(screen.getByText("unsubscribed")).toBeInTheDocument();
  });

  it("filters contacts by email search", () => {
    render(<ContactsTable contacts={mockContacts} lists={mockLists} />);
    const searchInput = screen.getByRole("searchbox", {
      name: /search contacts/i,
    });
    fireEvent.change(searchInput, { target: { value: "ops" } });
    expect(screen.queryByText(/founder\.alpha@example\.com/)).toBeNull();
    expect(screen.getByText(/ops\.beta@example\.com/)).toBeInTheDocument();
  });

  it("shows bulk bar when a contact is selected", () => {
    render(<ContactsTable contacts={mockContacts} lists={mockLists} />);
    const checkboxes = screen.getAllByRole("checkbox");
    fireEvent.click(checkboxes[1]!);
    expect(screen.getByText(/1 selected/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /unsubscribe/i })).toBeInTheDocument();
  });

  it("select all selects all visible contacts", () => {
    render(<ContactsTable contacts={mockContacts} lists={mockLists} />);
    const selectAll = screen.getByRole("checkbox", {
      name: /select all visible/i,
    });
    fireEvent.click(selectAll);
    expect(screen.getByText(/3 selected/)).toBeInTheDocument();
  });

  it("shows empty state when filter matches nothing", () => {
    render(<ContactsTable contacts={mockContacts} lists={mockLists} />);
    const searchInput = screen.getByRole("searchbox", {
      name: /search contacts/i,
    });
    fireEvent.change(searchInput, {
      target: { value: "zzz-no-match-xyz" },
    });
    expect(
      screen.getByText(/no contacts match the current filters/i),
    ).toBeInTheDocument();
  });
});

const mockContactDetail: ContactDetail = {
  id: "ctc-001",
  email: "founder.alpha@example.com",
  firstName: "Alex",
  lastName: "Founder",
  lifecycle: "active",
  source: "csv_import",
  suppressedAt: null,
  suppressionReason: null,
  createdAt: "2026-03-15T09:00:00Z",
  updatedAt: "2026-04-23T07:20:00Z",
  lists: [
    { listId: "lst-001", listName: "Early access", addedAt: "2026-03-16T10:00:00Z" },
  ],
  preferences: [
    { key: "newsletter", label: "Newsletter", subscribed: true },
    { key: "marketing", label: "Marketing", subscribed: false },
  ],
  recentEvents: [
    {
      id: "evt-001",
      type: "delivered",
      occurredAt: "2026-04-22T10:15:00Z",
      detail: "Campaign: April newsletter",
    },
  ],
};

describe("ContactDrawer", () => {
  it("renders contact email in header", () => {
    render(<ContactDrawer contact={mockContactDetail} />);
    const headings = screen.getAllByText("founder.alpha@example.com");
    expect(headings.length).toBeGreaterThan(0);
  });

  it("renders lifecycle badge", () => {
    render(<ContactDrawer contact={mockContactDetail} />);
    expect(screen.getByText("active")).toBeInTheDocument();
  });

  it("renders tab triggers for all four tabs", () => {
    render(<ContactDrawer contact={mockContactDetail} />);
    expect(screen.getByRole("tab", { name: "Overview" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /Lists/ })).toBeInTheDocument();
    expect(
      screen.getByRole("tab", { name: "Preferences" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /History/ })).toBeInTheDocument();
  });

  it("renders overview tab content by default", () => {
    render(<ContactDrawer contact={mockContactDetail} />);
    expect(screen.getByText("Contact ID")).toBeInTheDocument();
    expect(screen.getByText("ctc-001")).toBeInTheDocument();
    expect(screen.getByText("csv import")).toBeInTheDocument();
  });

  it("shows list membership count in tab trigger", () => {
    render(<ContactDrawer contact={mockContactDetail} />);
    expect(screen.getByRole("tab", { name: /Lists \(1\)/ })).toBeInTheDocument();
  });

  it("shows all four tab triggers", () => {
    render(<ContactDrawer contact={mockContactDetail} />);
    expect(screen.getByRole("tab", { name: "Preferences" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /History/ })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "Overview" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /Lists/ })).toBeInTheDocument();
  });

  it("shows history tab trigger with count", () => {
    render(<ContactDrawer contact={mockContactDetail} />);
    expect(
      screen.getByRole("tab", { name: /History \(1\)/ }),
    ).toBeInTheDocument();
  });
});
