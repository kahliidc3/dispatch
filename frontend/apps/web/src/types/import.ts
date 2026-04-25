export type ImportJobStatus = "pending" | "processing" | "completed" | "failed";

export type RejectionReason = "format" | "invalid_mx" | "role_account";

export type ImportJob = {
  id: string;
  status: ImportJobStatus;
  fileName: string;
  totalRows: number;
  processedRows: number;
  acceptedRows: number;
  rejectedRows: number;
  duplicateRows: number;
  createdAt: string;
  completedAt: string | null;
};

export type ImportJobError = {
  rowNumber: number;
  rawEmail: string;
  reason: RejectionReason;
  detail: string;
};

export type FieldMapping =
  | "email"
  | "first_name"
  | "last_name"
  | `pref:${string}`
  | "skip";

export type ColumnMapping = Record<string, FieldMapping>;
