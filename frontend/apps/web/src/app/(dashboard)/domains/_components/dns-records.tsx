"use client";

import { useState } from "react";
import { Check, Copy } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { formatTimestamp } from "@/lib/formatters";
import type { DnsRecord, DnsRecordStatus } from "@/types/domain";

const statusVariant: Record<DnsRecordStatus, "success" | "danger" | "muted"> =
  {
    valid: "success",
    invalid: "danger",
    pending: "muted",
  };

const purposeLabel: Record<DnsRecord["purpose"], string> = {
  spf: "SPF",
  dkim: "DKIM",
  dmarc: "DMARC",
  mail_from: "MAIL FROM",
};

async function writeToClipboard(value: string) {
  if (navigator.clipboard) {
    await navigator.clipboard.writeText(value);
    return;
  }
  // fallback for browsers without clipboard API
  const el = document.createElement("textarea");
  el.value = value;
  el.setAttribute("readonly", "");
  el.style.position = "absolute";
  el.style.left = "-9999px";
  document.body.appendChild(el);
  el.select();
  document.execCommand("copy");
  document.body.removeChild(el);
}

type DnsRecordsProps = {
  records: DnsRecord[];
};

export function DnsRecords({ records }: DnsRecordsProps) {
  const [copiedKey, setCopiedKey] = useState<string | null>(null);
  const [copiedAll, setCopiedAll] = useState(false);

  function markCopied(key: string, durationMs = 1500) {
    setCopiedKey(key);
    setTimeout(() => setCopiedKey((prev) => (prev === key ? null : prev)), durationMs);
  }

  async function handleCopyValue(recordId: string, value: string) {
    await writeToClipboard(value);
    markCopied(`${recordId}-value`);
  }

  async function handleCopyHostname(recordId: string, hostname: string) {
    await writeToClipboard(hostname);
    markCopied(`${recordId}-hostname`);
  }

  async function handleCopyAll() {
    const text = records
      .map(
        (r) =>
          `; ${purposeLabel[r.purpose]} (${r.type})\n${r.hostname}\t${r.type}\t${r.value}`,
      )
      .join("\n\n");
    await writeToClipboard(text);
    setCopiedAll(true);
    setTimeout(() => setCopiedAll(false), 1500);
  }

  return (
    <div className="grid gap-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="section-title">DNS records</h2>
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={() => void handleCopyAll()}
          aria-label={copiedAll ? "All records copied" : "Copy all DNS records"}
        >
          {copiedAll ? (
            <>
              <Check className="h-4 w-4" aria-hidden />
              All copied
            </>
          ) : (
            <>
              <Copy className="h-4 w-4" aria-hidden />
              Copy all
            </>
          )}
        </Button>
      </div>
      <div className="grid gap-3" role="list" aria-label="DNS records">
        {records.map((record) => (
          <div
            key={record.id}
            role="listitem"
            className="surface-panel-muted grid gap-3 p-4"
          >
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="flex flex-wrap items-center gap-2">
                <Badge variant="outline">{record.type}</Badge>
                <span className="text-sm font-medium">
                  {purposeLabel[record.purpose]}
                </span>
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <Badge variant={statusVariant[record.status]}>
                  {record.status}
                </Badge>
                {record.lastCheckedAt ? (
                  <span className="text-xs text-text-muted">
                    Checked {formatTimestamp(record.lastCheckedAt)}
                  </span>
                ) : (
                  <span className="text-xs text-text-muted">Not yet checked</span>
                )}
              </div>
            </div>

            <div className="grid gap-2">
              <div className="flex items-start gap-2">
                <span className="properties-label w-20 shrink-0 pt-0.5">Hostname</span>
                <div className="flex min-w-0 flex-1 items-start gap-2">
                  <code className="mono min-w-0 flex-1 break-all text-xs">
                    {record.hostname}
                  </code>
                  <button
                    type="button"
                    className="shrink-0 rounded p-0.5 text-text-muted transition-colors hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[color:var(--focus-ring)]"
                    aria-label={
                      copiedKey === `${record.id}-hostname`
                        ? "Hostname copied"
                        : "Copy hostname"
                    }
                    onClick={() =>
                      void handleCopyHostname(record.id, record.hostname)
                    }
                  >
                    {copiedKey === `${record.id}-hostname` ? (
                      <Check className="h-3.5 w-3.5" aria-hidden />
                    ) : (
                      <Copy className="h-3.5 w-3.5" aria-hidden />
                    )}
                  </button>
                </div>
              </div>

              <div className="flex items-start gap-2">
                <span className="properties-label w-20 shrink-0 pt-0.5">Value</span>
                <div className="flex min-w-0 flex-1 items-start gap-2">
                  <code className="mono min-w-0 flex-1 break-all text-xs">
                    {record.value}
                  </code>
                  <button
                    type="button"
                    className="shrink-0 rounded p-0.5 text-text-muted transition-colors hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[color:var(--focus-ring)]"
                    aria-label={
                      copiedKey === `${record.id}-value`
                        ? "Value copied"
                        : "Copy value"
                    }
                    onClick={() =>
                      void handleCopyValue(record.id, record.value)
                    }
                  >
                    {copiedKey === `${record.id}-value` ? (
                      <Check className="h-3.5 w-3.5" aria-hidden />
                    ) : (
                      <Copy className="h-3.5 w-3.5" aria-hidden />
                    )}
                  </button>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
