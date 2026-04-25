import type { ContactDetail, ContactListItem } from "@/types/contact";

const contactDetails: Record<string, ContactDetail> = {
  "ctc-001": {
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
      {
        listId: "lst-001",
        listName: "Early access",
        addedAt: "2026-03-16T10:00:00Z",
      },
      {
        listId: "lst-002",
        listName: "Newsletter",
        addedAt: "2026-03-20T14:30:00Z",
      },
    ],
    preferences: [
      { key: "newsletter", label: "Newsletter", subscribed: true },
      { key: "product_updates", label: "Product updates", subscribed: true },
      { key: "marketing", label: "Marketing", subscribed: false },
    ],
    recentEvents: [
      {
        id: "evt-001-1",
        type: "delivered",
        occurredAt: "2026-04-22T10:15:00Z",
        detail: "Campaign: April newsletter",
      },
      {
        id: "evt-001-2",
        type: "opened",
        occurredAt: "2026-04-22T10:42:00Z",
        detail: "Campaign: April newsletter",
      },
      {
        id: "evt-001-3",
        type: "clicked",
        occurredAt: "2026-04-22T11:05:00Z",
        detail: "Link: Product changelog",
      },
    ],
  },
  "ctc-002": {
    id: "ctc-002",
    email: "ops.beta@example.com",
    firstName: "Blake",
    lastName: "Ops",
    lifecycle: "suppressed",
    source: "manual",
    suppressedAt: "2026-04-22T18:15:00Z",
    suppressionReason: "Hard bounce on April newsletter",
    createdAt: "2026-03-20T12:00:00Z",
    updatedAt: "2026-04-22T18:15:00Z",
    lists: [
      {
        listId: "lst-001",
        listName: "Early access",
        addedAt: "2026-03-21T08:00:00Z",
      },
    ],
    preferences: [
      { key: "newsletter", label: "Newsletter", subscribed: false },
      { key: "product_updates", label: "Product updates", subscribed: false },
      { key: "marketing", label: "Marketing", subscribed: false },
    ],
    recentEvents: [
      {
        id: "evt-002-1",
        type: "bounced",
        occurredAt: "2026-04-22T18:10:00Z",
        detail: "Hard bounce — address does not exist",
      },
      {
        id: "evt-002-2",
        type: "sent",
        occurredAt: "2026-04-22T09:00:00Z",
        detail: "Campaign: April newsletter",
      },
    ],
  },
  "ctc-003": {
    id: "ctc-003",
    email: "hello.gamma@example.com",
    firstName: null,
    lastName: null,
    lifecycle: "unsubscribed",
    source: "api",
    suppressedAt: null,
    suppressionReason: null,
    createdAt: "2026-04-01T08:00:00Z",
    updatedAt: "2026-04-21T11:40:00Z",
    lists: [],
    preferences: [
      { key: "newsletter", label: "Newsletter", subscribed: false },
      { key: "product_updates", label: "Product updates", subscribed: false },
      { key: "marketing", label: "Marketing", subscribed: false },
    ],
    recentEvents: [
      {
        id: "evt-003-1",
        type: "unsubscribed",
        occurredAt: "2026-04-21T11:40:00Z",
        detail: "Via unsubscribe link in campaign email",
      },
      {
        id: "evt-003-2",
        type: "sent",
        occurredAt: "2026-04-21T09:00:00Z",
        detail: "Campaign: Product announcement",
      },
    ],
  },
  "ctc-004": {
    id: "ctc-004",
    email: "delta.test@example.com",
    firstName: "Dana",
    lastName: null,
    lifecycle: "complained",
    source: "webhook",
    suppressedAt: "2026-04-20T14:00:00Z",
    suppressionReason: "Spam complaint via feedback loop",
    createdAt: "2026-03-25T10:00:00Z",
    updatedAt: "2026-04-20T14:00:00Z",
    lists: [],
    preferences: [
      { key: "newsletter", label: "Newsletter", subscribed: false },
      { key: "product_updates", label: "Product updates", subscribed: false },
      { key: "marketing", label: "Marketing", subscribed: false },
    ],
    recentEvents: [
      {
        id: "evt-004-1",
        type: "complained",
        occurredAt: "2026-04-20T14:00:00Z",
        detail: "Spam complaint received via SES feedback loop",
      },
      {
        id: "evt-004-2",
        type: "delivered",
        occurredAt: "2026-04-19T10:00:00Z",
        detail: "Campaign: April newsletter",
      },
    ],
  },
};

export const contactList: ContactListItem[] = Object.values(contactDetails).map(
  (d) => ({
    id: d.id,
    email: d.email,
    firstName: d.firstName,
    lastName: d.lastName,
    lifecycle: d.lifecycle,
    source: d.source,
    createdAt: d.createdAt,
    updatedAt: d.updatedAt,
  }),
);

export function getContactDetail(id: string): ContactDetail | undefined {
  return contactDetails[id];
}
