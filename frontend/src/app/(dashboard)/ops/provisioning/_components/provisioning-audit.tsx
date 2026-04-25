"use client";

import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import { formatTimestamp } from "@/lib/formatters";
import type { ProvisioningAttempt, ProvisioningStatus } from "@/types/domain";

const statusVariant: Record<
  ProvisioningStatus,
  "success" | "danger" | "warning" | "muted"
> = {
  completed: "success",
  failed: "danger",
  in_progress: "warning",
  abandoned: "muted",
};

const providerLabel: Record<string, string> = {
  manual: "Manual",
  cloudflare: "Cloudflare",
  route53: "Route 53",
};

function formatDuration(
  startedAt: string,
  completedAt: string | null,
): string {
  if (!completedAt) return "—";
  const ms = new Date(completedAt).getTime() - new Date(startedAt).getTime();
  const secs = Math.floor(ms / 1000);
  if (secs < 60) return `${secs}s`;
  const mins = Math.floor(secs / 60);
  return `${mins}m ${secs % 60}s`;
}

type ProvisioningAuditProps = {
  attempts: ProvisioningAttempt[];
};

export function ProvisioningAudit({ attempts }: ProvisioningAuditProps) {
  const completedCount = attempts.filter(
    (a) => a.status === "completed",
  ).length;
  const failedCount = attempts.filter((a) => a.status === "failed").length;

  return (
    <div className="grid gap-4">
      <div className="flex items-center gap-4 text-sm text-text-muted">
        <span>{attempts.length} total</span>
        {completedCount > 0 && (
          <span className="text-success">{completedCount} completed</span>
        )}
        {failedCount > 0 && (
          <span className="text-danger">{failedCount} failed</span>
        )}
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border text-left text-text-muted">
              <th className="pb-2 pr-6 font-medium">Domain</th>
              <th className="pb-2 pr-6 font-medium">Provider</th>
              <th className="pb-2 pr-6 font-medium">Status</th>
              <th className="pb-2 pr-6 font-medium">Started</th>
              <th className="pb-2 pr-6 font-medium">Duration</th>
              <th className="pb-2 font-medium">Failure reason</th>
            </tr>
          </thead>
          <tbody>
            {attempts.map((attempt) => (
              <tr
                key={attempt.id}
                className="border-b border-border/50"
                aria-label={`${attempt.domainName} provisioning attempt`}
              >
                <td className="py-2 pr-6 font-medium">
                  <div className="flex flex-col gap-0.5">
                    <span>{attempt.domainName}</span>
                    {attempt.provider !== "manual" && (
                      <div className="flex gap-2">
                        <Link
                          href={`/domains/${attempt.domainId}`}
                          className="text-xs text-text-muted hover:underline"
                        >
                          Domain
                        </Link>
                        <Link
                          href={`/domains/${attempt.domainId}/provision`}
                          className="text-xs text-text-muted hover:underline"
                        >
                          Step log
                        </Link>
                      </div>
                    )}
                  </div>
                </td>
                <td className="py-2 pr-6 text-text-muted">
                  {providerLabel[attempt.provider] ?? attempt.provider}
                </td>
                <td className="py-2 pr-6">
                  <Badge variant={statusVariant[attempt.status]}>
                    {attempt.status.replace("_", " ")}
                  </Badge>
                </td>
                <td className="py-2 pr-6 text-text-muted">
                  {formatTimestamp(attempt.startedAt)}
                </td>
                <td className="py-2 pr-6 tabular-nums text-text-muted">
                  {formatDuration(attempt.startedAt, attempt.completedAt)}
                </td>
                <td className="py-2 text-text-muted">
                  {attempt.failureReason ? (
                    <span className="text-danger">
                      {attempt.failureReason.replace(/_/g, " ")}
                    </span>
                  ) : (
                    "—"
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
