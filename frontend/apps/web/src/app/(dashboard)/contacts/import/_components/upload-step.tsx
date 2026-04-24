"use client";

import { useRef, useState } from "react";
import { Button } from "@/components/ui/button";

const MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024; // 25 MB
const MAX_PREVIEW_ROWS = 5;

export type ParsedFile = {
  file: File;
  headers: string[];
  previewRows: string[][];
};

function parseCSV(text: string): { headers: string[]; rows: string[][] } {
  const lines = text.split(/\r?\n/).filter((l) => l.trim().length > 0);
  function splitLine(line: string): string[] {
    const fields: string[] = [];
    let current = "";
    let inQuotes = false;
    for (let i = 0; i < line.length; i++) {
      const char = line[i];
      if (char === '"') {
        inQuotes = !inQuotes;
      } else if (char === "," && !inQuotes) {
        fields.push(current.trim());
        current = "";
      } else {
        current += char;
      }
    }
    fields.push(current.trim());
    return fields;
  }
  const headers = splitLine(lines[0] ?? "");
  const rows = lines
    .slice(1, MAX_PREVIEW_ROWS + 1)
    .map((l) => splitLine(l));
  return { headers, rows };
}

type UploadStepProps = {
  onParsed: (parsed: ParsedFile) => void;
};

export function UploadStep({ onParsed }: UploadStepProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [parsed, setParsed] = useState<ParsedFile | null>(null);

  function handleFile(file: File) {
    setError(null);
    if (!file.name.endsWith(".csv")) {
      setError("Only .csv files are supported.");
      return;
    }
    if (file.size > MAX_FILE_SIZE_BYTES) {
      setError("File exceeds the 25 MB limit. Split it into smaller batches.");
      return;
    }
    const reader = new FileReader();
    reader.onload = (e) => {
      const text = e.target?.result;
      if (typeof text !== "string") return;
      const { headers, rows } = parseCSV(text);
      if (headers.length === 0 || !headers[0]) {
        setError("Could not detect column headers. Check the file format.");
        return;
      }
      const result: ParsedFile = { file, headers, previewRows: rows };
      setParsed(result);
    };
    reader.onerror = () => setError("Could not read the file.");
    reader.readAsText(file);
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  }

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
  }

  return (
    <div className="grid gap-6">
      <div
        role="button"
        tabIndex={0}
        aria-label="Drop zone: drag and drop a CSV file here, or click to browse"
        className={`flex min-h-48 cursor-pointer flex-col items-center justify-center gap-3 rounded-lg border-2 border-dashed p-8 transition-colors ${
          isDragging
            ? "border-primary bg-[color:color-mix(in_srgb,var(--accent)_8%,white)]"
            : "border-border hover:border-border-strong"
        }`}
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragEnter={() => setIsDragging(true)}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") inputRef.current?.click();
        }}
      >
        <div className="text-center">
          <p className="text-sm font-medium">Drop a CSV file here</p>
          <p className="mt-1 text-sm text-text-muted">
            or{" "}
            <span className="text-primary underline underline-offset-2">
              browse your files
            </span>
          </p>
        </div>
        <p className="text-xs text-text-muted">Max 25 MB · UTF-8 encoding</p>
        <input
          ref={inputRef}
          type="file"
          accept=".csv"
          className="sr-only"
          aria-hidden="true"
          onChange={handleChange}
        />
      </div>

      {error ? (
        <p role="alert" className="text-sm text-danger">
          {error}
        </p>
      ) : null}

      {parsed ? (
        <div className="grid gap-4">
          <div className="surface-panel-muted flex items-center justify-between gap-3 rounded-lg px-4 py-3">
            <div>
              <p className="text-sm font-medium">{parsed.file.name}</p>
              <p className="text-xs text-text-muted">
                {(parsed.file.size / 1024).toFixed(0)} KB ·{" "}
                {parsed.headers.length} column(s) detected
              </p>
            </div>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => {
                setParsed(null);
                if (inputRef.current) inputRef.current.value = "";
              }}
            >
              Remove
            </Button>
          </div>

          <div>
            <p className="mb-2 text-sm font-medium">Preview (first {Math.min(parsed.previewRows.length, MAX_PREVIEW_ROWS)} rows)</p>
            <div className="surface-panel overflow-x-auto">
              <table className="w-full text-sm" aria-label="CSV preview">
                <thead>
                  <tr className="border-b border-border">
                    {parsed.headers.map((h, i) => (
                      <th
                        key={i}
                        className="px-3 py-2 text-left font-medium text-text-muted"
                      >
                        {h || <span className="italic">(empty)</span>}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {parsed.previewRows.map((row, ri) => (
                    <tr key={ri} className="border-b border-border last:border-0">
                      {parsed.headers.map((_, ci) => (
                        <td
                          key={ci}
                          className="px-3 py-2 text-text-muted"
                        >
                          {row[ci] ?? ""}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="flex justify-end">
            <Button type="button" onClick={() => onParsed(parsed)}>
              Continue to column mapping
            </Button>
          </div>
        </div>
      ) : null}
    </div>
  );
}
