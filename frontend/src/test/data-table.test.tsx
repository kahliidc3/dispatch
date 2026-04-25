import { fireEvent, render, screen, within } from "@testing-library/react";
import type { ColumnDef } from "@tanstack/react-table";
import { describe, expect, it } from "vitest";
import { DataTable } from "@/components/shared/data-table";

type DemoRow = {
  count: number;
  name: string;
};

const headlessColumns: ColumnDef<DemoRow>[] = [
  {
    accessorKey: "name",
    header: "Name",
    cell: ({ row }) => row.original.name,
  },
  {
    accessorKey: "count",
    header: "Count",
    cell: ({ row }) => row.original.count,
  },
];

describe("DataTable", () => {
  it("renders legacy server-friendly row maps", () => {
    render(
      <DataTable
        caption="Legacy rows"
        columns={[
          { key: "name", label: "Name" },
          { key: "status", label: "Status" },
        ]}
        rows={[
          {
            name: "Warmup queue",
            status: "Ready",
          },
        ]}
      />,
    );

    expect(screen.getByRole("table", { name: "Legacy rows" })).toBeInTheDocument();
    expect(screen.getByText("Warmup queue")).toBeInTheDocument();
  });

  it("supports headless sorting and pagination", () => {
    render(
      <DataTable
        caption="Headless rows"
        columns={headlessColumns}
        data={[
          { name: "Bravo", count: 1 },
          { name: "Alpha", count: 3 },
          { name: "Charlie", count: 2 },
        ]}
        defaultPageSize={1}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /count/i }));
    fireEvent.click(screen.getByRole("button", { name: /count/i }));
    const rowsAfterSort = screen.getAllByRole("row");
    expect(within(rowsAfterSort[1]).getByText("Bravo")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /^next$/i }));
    const rowsAfterPageChange = screen.getAllByRole("row");
    expect(within(rowsAfterPageChange[1]).getByText("Charlie")).toBeInTheDocument();
  });
});
