import type { List, ListMember } from "@/types/list";

export const lists: List[] = [
  {
    id: "lst-001",
    name: "Early access",
    description: "Contacts who opted in to early feature access.",
    memberCount: 2,
    createdAt: "2026-04-01T10:00:00Z",
    updatedAt: "2026-04-23T08:00:00Z",
  },
  {
    id: "lst-002",
    name: "Newsletter",
    description: "Weekly product newsletter subscribers.",
    memberCount: 1,
    createdAt: "2026-04-05T09:00:00Z",
    updatedAt: "2026-04-23T09:00:00Z",
  },
  {
    id: "lst-003",
    name: "Beta testers",
    description: null,
    memberCount: 0,
    createdAt: "2026-04-15T11:00:00Z",
    updatedAt: "2026-04-15T11:00:00Z",
  },
];

const listMembers: Record<string, ListMember[]> = {
  "lst-001": [
    {
      contactId: "ctc-001",
      email: "founder.alpha@example.com",
      addedAt: "2026-03-16T10:00:00Z",
    },
    {
      contactId: "ctc-002",
      email: "ops.beta@example.com",
      addedAt: "2026-03-21T08:00:00Z",
    },
  ],
  "lst-002": [
    {
      contactId: "ctc-001",
      email: "founder.alpha@example.com",
      addedAt: "2026-03-20T14:30:00Z",
    },
  ],
  "lst-003": [],
};

export function getListById(id: string): List | undefined {
  return lists.find((l) => l.id === id);
}

export function getListMembers(id: string): ListMember[] {
  return listMembers[id] ?? [];
}
