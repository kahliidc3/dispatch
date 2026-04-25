import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { ConditionGroup } from "@/app/(dashboard)/segments/_components/condition-group";
import {
  validateDsl,
  ALLOWED_FIELDS,
  OPERATORS_BY_TYPE,
  getFieldDef,
  type SegmentDsl,
  type SegmentGroup,
} from "@/types/segment";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), refresh: vi.fn() }),
}));

vi.mock("sonner", () => ({ toast: { success: vi.fn(), error: vi.fn() } }));

vi.mock("@/lib/api/client", () => ({
  clientJson: vi.fn(),
}));

// ─── validateDsl ─────────────────────────────────────────────────────────────

describe("validateDsl", () => {
  it("returns null for a valid simple predicate", () => {
    const dsl: SegmentDsl = {
      type: "group",
      logic: "and",
      conditions: [
        { type: "predicate", field: "lifecycle_status", op: "eq", value: "active" },
      ],
    };
    expect(validateDsl(dsl)).toBeNull();
  });

  it("returns error for empty group", () => {
    const dsl: SegmentDsl = {
      type: "group",
      logic: "and",
      conditions: [],
    };
    expect(validateDsl(dsl)).toMatch(/at least one condition/i);
  });

  it("returns error for unknown field", () => {
    const dsl: SegmentDsl = {
      type: "group",
      logic: "and",
      conditions: [
        { type: "predicate", field: "unknown_field", op: "eq", value: "x" },
      ],
    };
    expect(validateDsl(dsl)).toMatch(/unknown field/i);
  });

  it("returns error for invalid operator for field type", () => {
    const dsl: SegmentDsl = {
      type: "group",
      logic: "and",
      conditions: [
        // boolean field with 'contains' operator (not valid for boolean)
        { type: "predicate", field: "pref:newsletter", op: "contains", value: "true" },
      ],
    };
    expect(validateDsl(dsl)).toMatch(/not valid/i);
  });

  it("returns null for nested group with valid predicates", () => {
    const dsl: SegmentDsl = {
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
    expect(validateDsl(dsl)).toBeNull();
  });

  it("returns error for empty nested group", () => {
    const dsl: SegmentDsl = {
      type: "group",
      logic: "and",
      conditions: [
        { type: "predicate", field: "lifecycle_status", op: "eq", value: "active" },
        { type: "group", logic: "or", conditions: [] },
      ],
    };
    expect(validateDsl(dsl)).toMatch(/at least one condition/i);
  });

  it("returns error when value is empty string", () => {
    const dsl: SegmentDsl = {
      type: "group",
      logic: "and",
      conditions: [
        { type: "predicate", field: "email", op: "contains", value: "" },
      ],
    };
    expect(validateDsl(dsl)).toMatch(/required/i);
  });
});

// ─── ALLOWED_FIELDS / OPERATORS_BY_TYPE ──────────────────────────────────────

describe("ALLOWED_FIELDS", () => {
  it("includes lifecycle_status as enum field", () => {
    const f = getFieldDef("lifecycle_status");
    expect(f).toBeDefined();
    expect(f?.type).toBe("enum");
    expect(f?.options).toContain("active");
  });

  it("includes email as string field", () => {
    const f = getFieldDef("email");
    expect(f?.type).toBe("string");
  });

  it("includes pref:newsletter as boolean field", () => {
    const f = getFieldDef("pref:newsletter");
    expect(f?.type).toBe("boolean");
  });

  it("returns undefined for unknown field", () => {
    expect(getFieldDef("not_a_real_field")).toBeUndefined();
  });
});

describe("OPERATORS_BY_TYPE", () => {
  it("string type has eq, neq, contains", () => {
    const ops = OPERATORS_BY_TYPE.string.map((o) => o.value);
    expect(ops).toContain("eq");
    expect(ops).toContain("neq");
    expect(ops).toContain("contains");
  });

  it("boolean type only has eq", () => {
    const ops = OPERATORS_BY_TYPE.boolean.map((o) => o.value);
    expect(ops).toEqual(["eq"]);
  });

  it("enum type has in operator", () => {
    const ops = OPERATORS_BY_TYPE.enum.map((o) => o.value);
    expect(ops).toContain("in");
  });

  it("number type has gt and lt", () => {
    const ops = OPERATORS_BY_TYPE.number.map((o) => o.value);
    expect(ops).toContain("gt");
    expect(ops).toContain("lt");
  });
});

// ─── ConditionGroup ───────────────────────────────────────────────────────────

const simpleGroup: SegmentGroup = {
  type: "group",
  logic: "and",
  conditions: [
    { type: "predicate", field: "lifecycle_status", op: "eq", value: "active" },
  ],
};

describe("ConditionGroup", () => {
  it("renders AND/OR toggle", () => {
    render(
      <ConditionGroup group={simpleGroup} onChange={vi.fn()} depth={0} />,
    );
    expect(screen.getByRole("button", { name: "AND" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "OR" })).toBeInTheDocument();
  });

  it("AND button is pressed when logic is and", () => {
    render(
      <ConditionGroup group={simpleGroup} onChange={vi.fn()} depth={0} />,
    );
    expect(screen.getByRole("button", { name: "AND" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    expect(screen.getByRole("button", { name: "OR" })).toHaveAttribute(
      "aria-pressed",
      "false",
    );
  });

  it("calls onChange with updated logic when OR is clicked", () => {
    const onChange = vi.fn();
    render(
      <ConditionGroup group={simpleGroup} onChange={onChange} depth={0} />,
    );
    fireEvent.click(screen.getByRole("button", { name: "OR" }));
    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({ logic: "or" }),
    );
  });

  it("renders field, operator, and value selects for each predicate", () => {
    render(
      <ConditionGroup group={simpleGroup} onChange={vi.fn()} depth={0} />,
    );
    expect(screen.getByRole("combobox", { name: "Condition field" })).toBeInTheDocument();
    expect(screen.getByRole("combobox", { name: "Condition operator" })).toBeInTheDocument();
  });

  it("shows Add condition button", () => {
    render(
      <ConditionGroup group={simpleGroup} onChange={vi.fn()} depth={0} />,
    );
    expect(
      screen.getByRole("button", { name: "+ Add condition" }),
    ).toBeInTheDocument();
  });

  it("shows Add group button at depth 0", () => {
    render(
      <ConditionGroup group={simpleGroup} onChange={vi.fn()} depth={0} />,
    );
    expect(
      screen.getByRole("button", { name: "+ Add group" }),
    ).toBeInTheDocument();
  });

  it("remove condition is disabled when only one predicate", () => {
    render(
      <ConditionGroup group={simpleGroup} onChange={vi.fn()} depth={0} />,
    );
    expect(
      screen.getByRole("button", { name: "Remove condition" }),
    ).toBeDisabled();
  });

  it("calls onChange with new condition when Add condition is clicked", () => {
    const onChange = vi.fn();
    render(
      <ConditionGroup group={simpleGroup} onChange={onChange} depth={0} />,
    );
    fireEvent.click(screen.getByRole("button", { name: "+ Add condition" }));
    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({
        conditions: expect.arrayContaining([
          expect.objectContaining({ type: "predicate" }),
          expect.objectContaining({ type: "predicate" }),
        ]),
      }),
    );
  });

  it("renders nested group when conditions include a group", () => {
    const groupWithNested: SegmentGroup = {
      type: "group",
      logic: "and",
      conditions: [
        { type: "predicate", field: "lifecycle_status", op: "eq", value: "active" },
        {
          type: "group",
          logic: "or",
          conditions: [
            { type: "predicate", field: "recent_event", op: "eq", value: "opened" },
          ],
        },
      ],
    };
    render(
      <ConditionGroup group={groupWithNested} onChange={vi.fn()} depth={0} />,
    );
    expect(
      screen.getByRole("button", { name: "Remove group" }),
    ).toBeInTheDocument();
  });

  it("shows all allowed fields in field select", () => {
    render(
      <ConditionGroup group={simpleGroup} onChange={vi.fn()} depth={0} />,
    );
    const fieldSelect = screen.getByRole("combobox", { name: "Condition field" });
    const options = Array.from(fieldSelect.querySelectorAll("option")).map(
      (o) => (o as HTMLOptionElement).value,
    );
    for (const field of ALLOWED_FIELDS) {
      expect(options).toContain(field.field);
    }
  });
});
