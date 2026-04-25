import type { ContactListItem } from "@/types/contact";

export type SegmentOperator = "eq" | "neq" | "in" | "gt" | "lt" | "contains";

export type SegmentFieldType = "string" | "enum" | "boolean" | "number";

export type SegmentFieldDef = {
  field: string;
  label: string;
  type: SegmentFieldType;
  options?: string[];
};

export type SegmentPredicate = {
  type: "predicate";
  field: string;
  op: SegmentOperator;
  value: string | string[] | number | boolean;
};

export type SegmentGroup = {
  type: "group";
  logic: "and" | "or";
  conditions: Array<SegmentPredicate | SegmentGroup>;
};

export type SegmentDsl = SegmentGroup;

export type Segment = {
  id: string;
  name: string;
  description: string | null;
  dslJson: SegmentDsl;
  lastComputedCount: number | null;
  lastComputedAt: string | null;
  isArchived: boolean;
  createdAt: string;
  updatedAt: string;
};

export type SegmentPreview = {
  count: number;
  exclusions: {
    suppressed: number;
    unsubscribed: number;
    bounced: number;
  };
  sample: ContactListItem[];
};

export const ALLOWED_FIELDS: SegmentFieldDef[] = [
  {
    field: "lifecycle_status",
    label: "Lifecycle status",
    type: "enum",
    options: ["active", "bounced", "complained", "unsubscribed", "suppressed", "deleted"],
  },
  {
    field: "source",
    label: "Source",
    type: "enum",
    options: ["csv_import", "api", "manual", "webhook"],
  },
  { field: "email", label: "Email", type: "string" },
  { field: "first_name", label: "First name", type: "string" },
  { field: "last_name", label: "Last name", type: "string" },
  {
    field: "pref:newsletter",
    label: "Pref: Newsletter",
    type: "boolean",
  },
  {
    field: "pref:product_updates",
    label: "Pref: Product updates",
    type: "boolean",
  },
  {
    field: "pref:marketing",
    label: "Pref: Marketing",
    type: "boolean",
  },
  {
    field: "recent_event",
    label: "Recent event",
    type: "enum",
    options: ["opened", "clicked", "bounced"],
  },
];

export const OPERATORS_BY_TYPE: Record<SegmentFieldType, Array<{ value: SegmentOperator; label: string }>> = {
  string: [
    { value: "eq", label: "is" },
    { value: "neq", label: "is not" },
    { value: "contains", label: "contains" },
  ],
  enum: [
    { value: "eq", label: "is" },
    { value: "neq", label: "is not" },
    { value: "in", label: "is one of" },
  ],
  boolean: [{ value: "eq", label: "is" }],
  number: [
    { value: "eq", label: "equals" },
    { value: "neq", label: "does not equal" },
    { value: "gt", label: "greater than" },
    { value: "lt", label: "less than" },
  ],
};

export function getFieldDef(field: string): SegmentFieldDef | undefined {
  return ALLOWED_FIELDS.find((f) => f.field === field);
}

export function validateDsl(dsl: SegmentDsl): string | null {
  function validateGroup(group: SegmentGroup): string | null {
    if (group.conditions.length === 0) {
      return "Each group must have at least one condition.";
    }
    for (const cond of group.conditions) {
      if (cond.type === "group") {
        const err = validateGroup(cond);
        if (err) return err;
      } else {
        const fieldDef = getFieldDef(cond.field);
        if (!fieldDef) return `Unknown field: ${cond.field}`;
        const validOps = OPERATORS_BY_TYPE[fieldDef.type].map((o) => o.value);
        if (!validOps.includes(cond.op)) {
          return `Operator "${cond.op}" is not valid for field "${cond.field}"`;
        }
        if (cond.value === "" || cond.value === null || cond.value === undefined) {
          return `Value is required for condition on "${fieldDef.label}"`;
        }
      }
    }
    return null;
  }
  return validateGroup(dsl);
}
