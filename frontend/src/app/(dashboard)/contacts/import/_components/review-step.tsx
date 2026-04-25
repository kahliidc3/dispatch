"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { DataTable } from "@/components/shared/data-table";
import { clientJson } from "@/lib/api/client";
import { apiEndpoints } from "@/lib/api/endpoints";
import type { ImportJob, ImportJobError, RejectionReason } from "@/types/import";

const reasonBadge: Record<RejectionReason, "danger" | "warning" | "muted"> = {
  format: "danger",
  invalid_mx: "warning",
  role_account: "muted",
};

const reasonLabel: Record<RejectionReason, string> = {
  format: "Bad format",
  invalid_mx: "No MX record",
  role_account: "Role address",
};

function exportErrorsCSV(errors: ImportJobError[], fileName: string) {
  const header = "row,email,reason,detail\n";
  const rows = errors
    .map(
      (e) =>
        `${e.rowNumber},"${e.rawEmail}","${e.reason}","${e.detail.replace(/"/g, '""')}"`,
    )
    .join("\n");
  const blob = new Blob([header + rows], { type: "text/csv" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `import-errors-${fileName.replace(/\.csv$/, "")}.csv`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

type ReviewStepProps = {
  job: ImportJob;
};

export function ReviewStep({ job }: ReviewStepProps) {
  const [errors, setErrors] = useState<ImportJobError[]>([]);
  const [loading, setLoading] = useState(true);
  const [fetchError, setFetchError] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        const result = await clientJson<ImportJobError[]>(
          apiEndpoints.contacts.importJobErrors(job.id),
        );
        setErrors(result);
      } catch {
        setFetchError(true);
      } finally {
        setLoading(false);
      }
    }
    void load();
  }, [job.id]);

  return (
    <div className="grid gap-6">
      <div className="surface-panel-muted grid grid-cols-2 gap-3 rounded-lg p-4 sm:grid-cols-4">
        <div className="text-center">
          <p className="text-lg font-semibold">
            {job.acceptedRows.toLocaleString()}
          </p>
          <p className="text-xs text-text-muted">Accepted</p>
        </div>
        <div className="text-center">
          <p className="text-lg font-semibold text-danger">
            {job.rejectedRows.toLocaleString()}
          </p>
          <p className="text-xs text-text-muted">Rejected</p>
        </div>
        <div className="text-center">
          <p className="text-lg font-semibold text-text-muted">
            {job.duplicateRows.toLocaleString()}
          </p>
          <p className="text-xs text-text-muted">Duplicates</p>
        </div>
        <div className="text-center">
          <p className="text-lg font-semibold">
            {job.totalRows.toLocaleString()}
          </p>
          <p className="text-xs text-text-muted">Total</p>
        </div>
      </div>

      {job.rejectedRows > 0 ? (
        <div className="grid gap-3">
          <div className="flex items-center justify-between gap-3">
            <p className="text-sm font-medium">
              Rejected rows ({job.rejectedRows.toLocaleString()})
            </p>
            {errors.length > 0 ? (
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => exportErrorsCSV(errors, job.fileName)}
              >
                Export CSV
              </Button>
            ) : null}
          </div>

          {loading ? (
            <p className="text-sm text-text-muted">Loading rejection details…</p>
          ) : fetchError ? (
            <p className="text-sm text-text-muted">
              Could not load rejection details. Try refreshing the page.
            </p>
          ) : (
            <DataTable
              columns={[
                { key: "row", label: "Row" },
                { key: "email", label: "Email" },
                { key: "reason", label: "Reason" },
                { key: "detail", label: "Detail" },
              ]}
              rows={errors.map((e) => ({
                row: (
                  <span className="mono text-sm text-text-muted">
                    #{e.rowNumber}
                  </span>
                ),
                email: (
                  <span className="mono text-sm">{e.rawEmail}</span>
                ),
                reason: (
                  <Badge variant={reasonBadge[e.reason]}>
                    {reasonLabel[e.reason]}
                  </Badge>
                ),
                detail: (
                  <span className="text-sm text-text-muted">{e.detail}</span>
                ),
              }))}
            />
          )}
        </div>
      ) : (
        <div className="surface-panel-muted rounded-lg p-4 text-center">
          <p className="font-medium">All rows accepted</p>
          <p className="mt-1 text-sm text-text-muted">
            No rejections — every contact passed validation.
          </p>
        </div>
      )}

      <div className="flex justify-end gap-3">
        <Button asChild variant="outline">
          <Link href="/contacts/import">Run another import</Link>
        </Button>
        <Button asChild>
          <Link href="/contacts">View contacts</Link>
        </Button>
      </div>
    </div>
  );
}
