import type { ContactRecord } from "@/types/contact";

export const contacts: ContactRecord[] = [
  {
    id: "ctc-001",
    email: "founder.alpha@example.com",
    lifecycle: "active",
    source: "csv_import",
    updatedAt: "2026-04-23T07:20:00Z",
  },
  {
    id: "ctc-002",
    email: "ops.beta@example.com",
    lifecycle: "suppressed",
    source: "manual",
    updatedAt: "2026-04-22T18:15:00Z",
  },
  {
    id: "ctc-003",
    email: "hello.gamma@example.com",
    lifecycle: "unsubscribed",
    source: "api",
    updatedAt: "2026-04-21T11:40:00Z",
  },
];

export function getContactById(contactId: string) {
  return contacts.find((contact) => contact.id === contactId) ?? contacts[0];
}
