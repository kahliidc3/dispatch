"use client";

import { useState, useMemo } from "react";
import Link from "next/link";
import { formatTimestamp } from "@/lib/formatters";
import { QUEUE_DEPTH_WARN_THRESHOLD } from "@/app/(dashboard)/ops/_lib/ops-queries";
import type { QueueRow } from "@/types/ops";

type SortKey = "domainName" | "queueDepth" | "oldestQueuedAgeSeconds" | "denialsPerMinute";

function formatAge(seconds: number | null): string {
  if (seconds === null) return "—";
  if (seconds < 60) return `${seconds}s`;
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  if (mins < 60) return `${mins}m ${secs}s`;
  const hrs = Math.floor(mins / 60);
  const remMins = mins % 60;
  return `${hrs}h ${remMins}m`;
}

type QueuesViewerProps = {
  initialRows: QueueRow[];
};

export function QueuesViewer({ initialRows }: QueuesViewerProps) {
  const [search, setSearch] = useState("");
  const [sortKey, setSortKey] = useState<SortKey>("queueDepth");
  const [sortDesc, setSortDesc] = useState(true);

  const updatedAt = initialRows[0]?.updatedAt ?? null;

  function toggleSort(key: SortKey) {
    if (sortKey === key) {
      setSortDesc((d) => !d);
    } else {
      setSortKey(key);
      setSortDesc(true);
    }
  }

  const rows = useMemo(() => {
    const filtered = search
      ? initialRows.filter((r) =>
          r.domainName.toLowerCase().includes(search.toLowerCase()),
        )
      : initialRows;

    return [...filtered].sort((a, b) => {
      const av = a[sortKey] ?? -1;
      const bv = b[sortKey] ?? -1;
      const cmp = av < bv ? -1 : av > bv ? 1 : 0;
      return sortDesc ? -cmp : cmp;
    });
  }, [initialRows, search, sortKey, sortDesc]);

  const warningCount = rows.filter(
    (r) => r.queueDepth > QUEUE_DEPTH_WARN_THRESHOLD,
  ).length;

  function sortIndicator(key: SortKey) {
    if (sortKey !== key) return null;
    return sortDesc ? " ▼" : " ▲";
  }

  return (
    <div className="grid gap-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          {warningCount > 0 && (
            <span
              role="status"
              className="text-sm font-medium text-warning"
              aria-label={`${warningCount} queue${warningCount > 1 ? "s" : ""} over depth threshold`}
            >
              {warningCount} queue{warningCount > 1 ? "s" : ""} over threshold
            </span>
          )}
        </div>
        <div className="flex items-center gap-3">
          {updatedAt && (
            <span className="text-xs text-text-muted">
              Last updated {formatTimestamp(updatedAt)}
            </span>
          )}
          <input
            type="search"
            placeholder="Search domain…"
            aria-label="Search domain"
            className="h-8 rounded-md border border-border bg-background px-3 text-sm placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-[color:var(--focus-ring)] w-48"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </div>

      {rows.length === 0 ? (
        <p className="text-sm text-text-muted">No queues match your search.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border text-left text-text-muted">
                <th className="pb-2 pr-6 font-medium">
                  <button
                    type="button"
                    className="hover:text-foreground"
                    onClick={() => toggleSort("domainName")}
                  >
                    Domain{sortIndicator("domainName")}
                  </button>
                </th>
                <th className="pb-2 pr-6 font-medium">Queue</th>
                <th className="pb-2 pr-6 text-right font-medium">Workers</th>
                <th className="pb-2 pr-6 text-right font-medium">
                  <button
                    type="button"
                    className="hover:text-foreground"
                    onClick={() => toggleSort("queueDepth")}
                  >
                    Depth{sortIndicator("queueDepth")}
                  </button>
                </th>
                <th className="pb-2 pr-6 text-right font-medium">
                  <button
                    type="button"
                    className="hover:text-foreground"
                    onClick={() => toggleSort("oldestQueuedAgeSeconds")}
                  >
                    Oldest age{sortIndicator("oldestQueuedAgeSeconds")}
                  </button>
                </th>
                <th className="pb-2 text-right font-medium">
                  <button
                    type="button"
                    className="hover:text-foreground"
                    onClick={() => toggleSort("denialsPerMinute")}
                  >
                    Denials/min{sortIndicator("denialsPerMinute")}
                  </button>
                </th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => {
                const isWarning = row.queueDepth > QUEUE_DEPTH_WARN_THRESHOLD;
                return (
                  <tr
                    key={row.domainId}
                    className={`border-b border-border/50 ${isWarning ? "bg-warning/5" : ""}`}
                    aria-label={`${row.domainName} queue`}
                  >
                    <td className="py-2 pr-6 font-medium">
                      <Link
                        href={`/domains/${row.domainId}?tab=throughput`}
                        className="hover:underline"
                      >
                        {row.domainName}
                      </Link>
                    </td>
                    <td className="py-2 pr-6 text-text-muted">
                      <code className="text-xs">{row.queueName}</code>
                    </td>
                    <td className="py-2 pr-6 text-right tabular-nums">
                      {row.workerCount}
                    </td>
                    <td
                      className={`py-2 pr-6 text-right tabular-nums font-medium ${isWarning ? "text-warning" : ""}`}
                    >
                      {row.queueDepth.toLocaleString()}
                    </td>
                    <td className="py-2 pr-6 text-right tabular-nums text-text-muted">
                      {formatAge(row.oldestQueuedAgeSeconds)}
                    </td>
                    <td
                      className={`py-2 text-right tabular-nums ${row.denialsPerMinute > 0 ? "text-warning" : "text-text-muted"}`}
                    >
                      {row.denialsPerMinute.toFixed(1)}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
