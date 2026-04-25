import type { Segment, SegmentDsl } from "@/types/segment";

const dslActiveNewsletter: SegmentDsl = {
  type: "group",
  logic: "and",
  conditions: [
    { type: "predicate", field: "lifecycle_status", op: "eq", value: "active" },
    { type: "predicate", field: "pref:newsletter", op: "eq", value: true },
  ],
};

const dslRecentOpeners: SegmentDsl = {
  type: "group",
  logic: "and",
  conditions: [
    { type: "predicate", field: "lifecycle_status", op: "eq", value: "active" },
    {
      type: "group",
      logic: "or",
      conditions: [
        { type: "predicate", field: "recent_event", op: "eq", value: "opened" },
        { type: "predicate", field: "recent_event", op: "eq", value: "clicked" },
      ],
    },
  ],
};

const dslApiContacts: SegmentDsl = {
  type: "group",
  logic: "and",
  conditions: [
    { type: "predicate", field: "source", op: "in", value: ["api", "webhook"] },
    { type: "predicate", field: "lifecycle_status", op: "neq", value: "suppressed" },
  ],
};

export const mockSegments: Segment[] = [
  {
    id: "seg-001",
    name: "Active newsletter subscribers",
    description: "All active contacts who opted in to newsletter",
    dslJson: dslActiveNewsletter,
    lastComputedCount: 12_847,
    lastComputedAt: "2026-04-20T08:00:00Z",
    isArchived: false,
    createdAt: "2026-02-01T10:00:00Z",
    updatedAt: "2026-04-20T08:00:00Z",
  },
  {
    id: "seg-002",
    name: "Recent openers or clickers",
    description: null,
    dslJson: dslRecentOpeners,
    lastComputedCount: 4_210,
    lastComputedAt: "2026-04-19T12:00:00Z",
    isArchived: false,
    createdAt: "2026-03-10T11:00:00Z",
    updatedAt: "2026-04-19T12:00:00Z",
  },
  {
    id: "seg-003",
    name: "API and webhook contacts",
    description: "Contacts added via API or webhook, excluding suppressed",
    dslJson: dslApiContacts,
    lastComputedCount: 8_532,
    lastComputedAt: "2026-04-18T09:00:00Z",
    isArchived: false,
    createdAt: "2026-03-15T09:00:00Z",
    updatedAt: "2026-04-18T09:00:00Z",
  },
];

export function getSegmentById(id: string): Segment | undefined {
  return mockSegments.find((s) => s.id === id);
}

export function newEmptyDsl(): SegmentDsl {
  return {
    type: "group",
    logic: "and",
    conditions: [
      { type: "predicate", field: "lifecycle_status", op: "eq", value: "active" },
    ],
  };
}
