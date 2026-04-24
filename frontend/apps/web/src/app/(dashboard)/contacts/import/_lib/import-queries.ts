import type { ImportJob, ImportJobError } from "@/types/import";

export const mockCompletedJob: ImportJob = {
  id: "job-001",
  status: "completed",
  fileName: "contacts_april.csv",
  totalRows: 1000,
  processedRows: 1000,
  acceptedRows: 950,
  rejectedRows: 42,
  duplicateRows: 8,
  createdAt: "2026-04-24T10:00:00Z",
  completedAt: "2026-04-24T10:05:22Z",
};

export const mockProcessingJob: ImportJob = {
  id: "job-002",
  status: "processing",
  fileName: "contacts_april.csv",
  totalRows: 1000,
  processedRows: 430,
  acceptedRows: 410,
  rejectedRows: 18,
  duplicateRows: 2,
  createdAt: "2026-04-24T10:00:00Z",
  completedAt: null,
};

export const mockJobErrors: ImportJobError[] = [
  {
    rowNumber: 5,
    rawEmail: "ba**@",
    reason: "format",
    detail: "Email address has no domain",
  },
  {
    rowNumber: 12,
    rawEmail: "no**@noreply.example.com",
    reason: "role_account",
    detail: "noreply@ is a role-based address",
  },
  {
    rowNumber: 19,
    rawEmail: "te**@invalid-domain-xyz.com",
    reason: "invalid_mx",
    detail: "Domain has no valid MX records",
  },
  {
    rowNumber: 24,
    rawEmail: "ad**@example.com",
    reason: "role_account",
    detail: "admin@ is a role-based address",
  },
  {
    rowNumber: 31,
    rawEmail: "@@broken",
    reason: "format",
    detail: "Malformed email address",
  },
];
