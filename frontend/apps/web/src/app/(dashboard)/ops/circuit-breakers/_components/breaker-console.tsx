"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import Link from "next/link";
import { ChevronDown, ChevronRight } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { formatTimestamp } from "@/lib/formatters";
import {
  getBreakerMatrix,
  getBreakerTimeline,
} from "@/app/(dashboard)/ops/_lib/ops-queries";
import { ResetDialog } from "./reset-dialog";
import type { BreakerEntry, BreakerEntryState, BreakerScope, BreakerTripEvent } from "@/types/ops";

const POLL_INTERVAL_MS = 10_000;

const scopeOrder: BreakerScope[] = ["domain", "ip_pool", "sender_profile", "account"];
const scopeLabel: Record<BreakerScope, string> = {
  domain: "Domain",
  ip_pool: "IP pool",
  sender_profile: "Sender profile",
  account: "Account",
};

const thresholdInfo: Record<BreakerScope, string> = {
  domain: "Bounce > 1.5% or Complaint > 0.05%",
  ip_pool: "Bounce > 2% or Complaint > 0.07%",
  sender_profile: "Bounce > 1.5% or Complaint > 0.05%",
  account: "Bounce > 2.5% or Complaint > 0.08%",
};

const reasonLabel: Record<string, string> = {
  high_bounce_rate: "High bounce rate",
  high_complaint_rate: "High complaint rate",
};

const stateVariant: Record<
  BreakerEntryState,
  "danger" | "warning" | "success"
> = {
  open: "danger",
  half_open: "warning",
  closed: "success",
};

type FilterValue = "all" | "open" | "last_24h" | "high_bounce_rate" | "high_complaint_rate";

const FILTER_OPTIONS: { value: FilterValue; label: string }[] = [
  { value: "all", label: "All" },
  { value: "open", label: "Open only" },
  { value: "last_24h", label: "Last 24h" },
  { value: "high_bounce_rate", label: "High bounce" },
  { value: "high_complaint_rate", label: "High complaint" },
];

function isWithin24h(ts: string | null): boolean {
  if (!ts) return false;
  return Date.now() - new Date(ts).getTime() < 24 * 60 * 60 * 1000;
}

type BreakerConsoleProps = {
  initialEntries: BreakerEntry[];
};

export function BreakerConsole({ initialEntries }: BreakerConsoleProps) {
  const [entries, setEntries] = useState<BreakerEntry[]>(initialEntries);
  const [filter, setFilter] = useState<FilterValue>("all");
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [timelines, setTimelines] = useState<Record<string, BreakerTripEvent[]>>({});
  const [resetEntry, setResetEntry] = useState<BreakerEntry | null>(null);
  const [updatedAt, setUpdatedAt] = useState<string>(
    new Date().toISOString(),
  );

  const pollTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const isHiddenRef = useRef(false);

  const poll = useCallback(() => {
    if (isHiddenRef.current) return;
    const fresh = getBreakerMatrix();
    setEntries(fresh);
    setUpdatedAt(new Date().toISOString());
  }, []);

  useEffect(() => {
    pollTimerRef.current = setInterval(poll, POLL_INTERVAL_MS);

    function onVisibility() {
      isHiddenRef.current = document.visibilityState === "hidden";
      if (!isHiddenRef.current) poll();
    }
    document.addEventListener("visibilitychange", onVisibility);

    return () => {
      if (pollTimerRef.current) clearInterval(pollTimerRef.current);
      document.removeEventListener("visibilitychange", onVisibility);
    };
  }, [poll]);

  function toggleExpand(id: string) {
    if (expandedId === id) {
      setExpandedId(null);
      return;
    }
    setExpandedId(id);
    if (!timelines[id]) {
      setTimelines((prev) => ({ ...prev, [id]: getBreakerTimeline(id) }));
    }
  }

  function handleReset(breakerId: string) {
    setEntries((prev) =>
      prev.map((e) =>
        e.id === breakerId
          ? { ...e, state: "closed", trippedAt: null, reason: null }
          : e,
      ),
    );
    setResetEntry(null);
  }

  const filtered = entries.filter((e) => {
    if (filter === "open") return e.state === "open";
    if (filter === "last_24h") return isWithin24h(e.trippedAt);
    if (filter === "high_bounce_rate") return e.reason === "high_bounce_rate";
    if (filter === "high_complaint_rate") return e.reason === "high_complaint_rate";
    return true;
  });

  const grouped = scopeOrder.reduce<Record<BreakerScope, BreakerEntry[]>>(
    (acc, scope) => {
      acc[scope] = filtered.filter((e) => e.scope === scope);
      return acc;
    },
    { domain: [], ip_pool: [], sender_profile: [], account: [] },
  );

  const openCount = entries.filter((e) => e.state === "open").length;

  return (
    <div className="grid gap-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-2">
          {FILTER_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              type="button"
              onClick={() => setFilter(opt.value)}
              aria-pressed={filter === opt.value}
              className={`rounded-full border px-3 py-1 text-xs font-medium transition-colors ${
                filter === opt.value
                  ? "border-primary bg-primary text-primary-foreground"
                  : "border-border text-text-muted hover:text-foreground"
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-3">
          {openCount > 0 && (
            <span
              role="status"
              aria-label={`${openCount} open breaker${openCount > 1 ? "s" : ""}`}
              className="text-sm font-medium text-danger"
            >
              {openCount} open
            </span>
          )}
          <span className="text-xs text-text-muted">
            Updated {formatTimestamp(updatedAt)}
          </span>
        </div>
      </div>

      {scopeOrder.map((scope) => {
        const scopeRows = grouped[scope];
        if (scopeRows.length === 0) return null;

        return (
          <section key={scope} aria-label={`${scopeLabel[scope]} breakers`}>
            <div className="mb-2 flex items-center gap-2">
              <h2 className="section-title">{scopeLabel[scope]}</h2>
              <span className="text-xs text-text-muted">
                {thresholdInfo[scope]}
              </span>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border text-left text-text-muted">
                    <th className="pb-2 pr-4 font-medium">Entity</th>
                    <th className="pb-2 pr-4 font-medium">State</th>
                    <th className="pb-2 pr-4 font-medium">Tripped at</th>
                    <th className="pb-2 pr-4 font-medium">Reason</th>
                    <th className="pb-2 pr-4 font-medium">Auto-reset</th>
                    <th className="pb-2 font-medium"></th>
                  </tr>
                </thead>
                <tbody>
                  {scopeRows.map((entry) => (
                    <>
                      <tr
                        key={entry.id}
                        className={`border-b border-border/50 ${entry.state === "open" ? "bg-danger/5" : ""}`}
                      >
                        <td className="py-2 pr-4 font-medium">
                          <div className="flex items-center gap-1.5">
                            <button
                              type="button"
                              aria-expanded={expandedId === entry.id}
                              aria-controls={`timeline-${entry.id}`}
                              onClick={() => toggleExpand(entry.id)}
                              className="text-text-muted hover:text-foreground"
                            >
                              {expandedId === entry.id ? (
                                <ChevronDown className="h-3.5 w-3.5" aria-hidden />
                              ) : (
                                <ChevronRight className="h-3.5 w-3.5" aria-hidden />
                              )}
                            </button>
                            <Link
                              href={entry.entityHref}
                              className="hover:underline"
                            >
                              {entry.entityName}
                            </Link>
                          </div>
                        </td>
                        <td className="py-2 pr-4">
                          <Badge variant={stateVariant[entry.state]}>
                            {entry.state}
                          </Badge>
                        </td>
                        <td className="py-2 pr-4 text-text-muted">
                          {entry.trippedAt
                            ? formatTimestamp(entry.trippedAt)
                            : "—"}
                        </td>
                        <td className="py-2 pr-4">
                          {entry.reason ? (
                            <span className="text-warning">
                              {reasonLabel[entry.reason] ?? entry.reason}
                              {entry.bounceRatePct !== null && (
                                <span className="ml-1 text-text-muted">
                                  ({entry.bounceRatePct.toFixed(2)}%)
                                </span>
                              )}
                              {entry.complaintRatePct !== null && (
                                <span className="ml-1 text-text-muted">
                                  ({entry.complaintRatePct.toFixed(3)}%)
                                </span>
                              )}
                            </span>
                          ) : (
                            <span className="text-text-muted">—</span>
                          )}
                        </td>
                        <td className="py-2 pr-4 text-text-muted">
                          {entry.autoResetAt
                            ? formatTimestamp(entry.autoResetAt)
                            : entry.state === "open"
                              ? "Manual only"
                              : "—"}
                        </td>
                        <td className="py-2">
                          {entry.state === "open" && (
                            <Button
                              type="button"
                              size="sm"
                              variant="outline"
                              onClick={() => setResetEntry(entry)}
                            >
                              Reset
                            </Button>
                          )}
                        </td>
                      </tr>
                      {expandedId === entry.id && (
                        <tr key={`${entry.id}-timeline`}>
                          <td colSpan={6} className="pb-3 pl-6 pr-4">
                            <div
                              id={`timeline-${entry.id}`}
                              className="surface-panel-muted mt-1 rounded-md p-3"
                            >
                              <h3 className="mb-3 text-xs font-semibold uppercase tracking-wide text-text-muted">
                                Trip timeline
                              </h3>
                              <TripTimeline
                                events={timelines[entry.id] ?? []}
                              />
                            </div>
                          </td>
                        </tr>
                      )}
                    </>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        );
      })}

      {filtered.length === 0 && (
        <p className="text-sm text-text-muted">
          No circuit breakers match the current filter.
        </p>
      )}

      <ResetDialog
        entry={resetEntry}
        onClose={() => setResetEntry(null)}
        onReset={handleReset}
      />
    </div>
  );
}

function TripTimeline({ events }: { events: BreakerTripEvent[] }) {
  if (events.length === 0) {
    return <p className="text-sm text-text-muted">No history recorded.</p>;
  }

  const eventVariant: Record<
    BreakerTripEvent["type"],
    "danger" | "success" | "muted"
  > = {
    tripped: "danger",
    reset: "success",
    auto_reset: "muted",
  };

  const eventLabel: Record<BreakerTripEvent["type"], string> = {
    tripped: "Tripped",
    reset: "Reset",
    auto_reset: "Auto-reset",
  };

  return (
    <ol className="grid gap-2">
      {events.map((ev) => (
        <li key={ev.id} className="flex flex-wrap items-start gap-3 text-sm">
          <Badge variant={eventVariant[ev.type]}>{eventLabel[ev.type]}</Badge>
          <span className="text-text-muted">{formatTimestamp(ev.occurredAt)}</span>
          {ev.actor && (
            <span className="text-text-muted">by {ev.actor}</span>
          )}
          {ev.bounceRatePct !== null && (
            <span className="text-warning">bounce {ev.bounceRatePct.toFixed(2)}%</span>
          )}
          {ev.complaintRatePct !== null && (
            <span className="text-warning">
              complaint {ev.complaintRatePct.toFixed(3)}%
            </span>
          )}
          {ev.justification && (
            <span className="text-text-muted italic">
              &ldquo;{ev.justification}&rdquo;
            </span>
          )}
        </li>
      ))}
    </ol>
  );
}
