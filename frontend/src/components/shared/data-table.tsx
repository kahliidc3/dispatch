"use client";
"use no memo";

import {
  flexRender,
  getCoreRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  useReactTable,
  type ColumnDef,
  type SortingState,
} from "@tanstack/react-table";
import { ArrowDownUp, ChevronDown, ChevronLeft, ChevronRight, ChevronUp } from "lucide-react";
import { useMemo, useState, type ReactNode } from "react";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCaption,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { cn } from "@/lib/utils";

type LegacyColumn = {
  key: string;
  label: string;
  className?: string;
};

type LegacyRow = Record<string, ReactNode>;

type LegacyDataTableProps = {
  caption?: string;
  columns: LegacyColumn[];
  rows: LegacyRow[];
  emptyState?: ReactNode;
  className?: string;
};

type KeysetPagination = {
  hasNextPage: boolean;
  hasPreviousPage?: boolean;
  startCursor?: string | null;
  endCursor?: string | null;
  onNextPage?: (cursor: string | null) => void;
  onPreviousPage?: (cursor: string | null) => void;
};

type HeadlessDataTableProps<TData> = {
  caption?: string;
  columns: ColumnDef<TData, unknown>[];
  data: TData[];
  emptyState?: ReactNode;
  className?: string;
  defaultPageSize?: number;
  pageSizeOptions?: number[];
  initialSorting?: SortingState;
  getRowId?: (row: TData, index: number) => string;
  keysetPagination?: KeysetPagination;
};

type DataTableProps<TData> = LegacyDataTableProps | HeadlessDataTableProps<TData>;

function LegacyDataTable({
  caption,
  columns,
  rows,
  emptyState,
  className,
}: LegacyDataTableProps) {
  return (
    <div className={cn("surface-panel overflow-hidden", className)}>
      <Table>
        {caption ? <TableCaption>{caption}</TableCaption> : null}
        <TableHeader>
          <TableRow>
            {columns.map((column) => (
              <TableHead key={column.key} className={column.className}>
                {column.label}
              </TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {rows.length > 0 ? (
            rows.map((row, index) => (
              <TableRow key={index}>
                {columns.map((column) => (
                  <TableCell key={column.key} className={column.className}>
                    {row[column.key]}
                  </TableCell>
                ))}
              </TableRow>
            ))
          ) : (
            <TableRow>
              <TableCell colSpan={columns.length} className="px-4 py-10">
                {emptyState ?? (
                  <div className="text-sm text-text-muted">No rows available.</div>
                )}
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </div>
  );
}

function SortIndicator({ direction }: { direction: false | "asc" | "desc" }) {
  if (direction === "asc") {
    return <ChevronUp className="h-4 w-4" />;
  }

  if (direction === "desc") {
    return <ChevronDown className="h-4 w-4" />;
  }

  return <ArrowDownUp className="h-4 w-4" />;
}

function HeadlessDataTable<TData>({
  caption,
  columns,
  data,
  emptyState,
  className,
  defaultPageSize = 10,
  pageSizeOptions = [10, 25, 50],
  initialSorting = [],
  getRowId,
  keysetPagination,
}: HeadlessDataTableProps<TData>) {
  const [sorting, setSorting] = useState<SortingState>(initialSorting);
  const [pageSize, setPageSize] = useState(defaultPageSize);
  // eslint-disable-next-line react-hooks/incompatible-library
  const table = useReactTable({
    columns,
    data,
    getCoreRowModel: getCoreRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getRowId,
    initialState: {
      pagination: {
        pageIndex: 0,
        pageSize: defaultPageSize,
      },
      sorting: initialSorting,
    },
    onSortingChange: setSorting,
    state: {
      sorting,
    },
  });
  const rows = table.getRowModel().rows;
  const visiblePageSizeOptions = useMemo(
    () => Array.from(new Set([defaultPageSize, ...pageSizeOptions])).sort((a, b) => a - b),
    [defaultPageSize, pageSizeOptions],
  );

  return (
    <div className={cn("surface-panel overflow-hidden", className)}>
      <Table>
        {caption ? <TableCaption>{caption}</TableCaption> : null}
        <TableHeader>
          {table.getHeaderGroups().map((headerGroup) => (
            <TableRow key={headerGroup.id}>
              {headerGroup.headers.map((header) => {
                const canSort = header.column.getCanSort();

                return (
                  <TableHead key={header.id}>
                    {header.isPlaceholder ? null : canSort ? (
                      <button
                        type="button"
                        className="inline-flex items-center gap-1 font-medium text-text-muted transition-colors hover:text-foreground"
                        onClick={header.column.getToggleSortingHandler()}
                      >
                        {flexRender(
                          header.column.columnDef.header,
                          header.getContext(),
                        )}
                        <SortIndicator direction={header.column.getIsSorted()} />
                      </button>
                    ) : (
                      flexRender(
                        header.column.columnDef.header,
                        header.getContext(),
                      )
                    )}
                  </TableHead>
                );
              })}
            </TableRow>
          ))}
        </TableHeader>
        <TableBody>
          {rows.length > 0 ? (
            rows.map((row) => (
              <TableRow key={row.id}>
                {row.getVisibleCells().map((cell) => (
                  <TableCell key={cell.id}>
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </TableCell>
                ))}
              </TableRow>
            ))
          ) : (
            <TableRow>
              <TableCell colSpan={columns.length} className="px-4 py-10">
                {emptyState ?? (
                  <div className="text-sm text-text-muted">No rows available.</div>
                )}
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
      <div className="flex flex-wrap items-center justify-between gap-3 border-t border-border px-4 py-3">
        <div className="flex flex-wrap items-center gap-3 text-sm text-text-muted">
          <span>{data.length} row(s)</span>
          <label className="flex items-center gap-2">
            <span>Rows per page</span>
            <select
              className="field h-9 w-20"
              aria-label="Rows per page"
              value={pageSize}
              onChange={(event) => {
                const nextPageSize = Number(event.target.value);
                setPageSize(nextPageSize);
                table.setPageSize(nextPageSize);
              }}
            >
              {visiblePageSizeOptions.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </label>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {keysetPagination ? (
            <>
              <Button
                type="button"
                variant="outline"
                size="sm"
                disabled={!keysetPagination.hasPreviousPage}
                onClick={() => keysetPagination.onPreviousPage?.(keysetPagination.startCursor ?? null)}
              >
                <ChevronLeft className="h-4 w-4" />
                Previous
              </Button>
              <Button
                type="button"
                variant="outline"
                size="sm"
                disabled={!keysetPagination.hasNextPage}
                onClick={() => keysetPagination.onNextPage?.(keysetPagination.endCursor ?? null)}
              >
                Next
                <ChevronRight className="h-4 w-4" />
              </Button>
            </>
          ) : (
            <>
              <Button
                type="button"
                variant="outline"
                size="sm"
                disabled={!table.getCanPreviousPage()}
                onClick={() => table.previousPage()}
              >
                <ChevronLeft className="h-4 w-4" />
                Previous
              </Button>
              <Button
                type="button"
                variant="outline"
                size="sm"
                disabled={!table.getCanNextPage()}
                onClick={() => table.nextPage()}
              >
                Next
                <ChevronRight className="h-4 w-4" />
              </Button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export function DataTable<TData>(props: DataTableProps<TData>) {
  if ("rows" in props) {
    return <LegacyDataTable {...props} />;
  }

  return <HeadlessDataTable {...props} />;
}
