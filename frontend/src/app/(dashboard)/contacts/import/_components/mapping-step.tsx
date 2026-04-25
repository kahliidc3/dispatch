"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import type { ColumnMapping, FieldMapping } from "@/types/import";

const TEMPLATE_KEY = "dispatch:import-mapping-template";

const KNOWN_FIELDS: Array<{ value: FieldMapping; label: string }> = [
  { value: "skip", label: "Skip" },
  { value: "email", label: "Email (required)" },
  { value: "first_name", label: "First name" },
  { value: "last_name", label: "Last name" },
  { value: "pref:newsletter", label: "Preference: Newsletter" },
  { value: "pref:product_updates", label: "Preference: Product updates" },
  { value: "pref:marketing", label: "Preference: Marketing" },
];

function autoDetect(header: string): FieldMapping {
  const h = header.toLowerCase().replace(/[\s_-]/g, "");
  if (h === "email" || h === "emailaddress") return "email";
  if (h === "firstname" || h === "fname") return "first_name";
  if (h === "lastname" || h === "lname") return "last_name";
  if (h === "newsletter") return "pref:newsletter";
  if (h === "productupdates") return "pref:product_updates";
  if (h === "marketing") return "pref:marketing";
  return "skip";
}

export function buildInitialMapping(headers: string[]): ColumnMapping {
  return Object.fromEntries(headers.map((h) => [h, autoDetect(h)]));
}

function loadTemplate(): ColumnMapping | null {
  try {
    const stored = localStorage.getItem(TEMPLATE_KEY);
    return stored ? (JSON.parse(stored) as ColumnMapping) : null;
  } catch {
    return null;
  }
}

function saveTemplate(mapping: ColumnMapping) {
  try {
    localStorage.setItem(TEMPLATE_KEY, JSON.stringify(mapping));
  } catch {}
}

type MappingStepProps = {
  headers: string[];
  initialMapping: ColumnMapping;
  onBack: () => void;
  onSubmit: (mapping: ColumnMapping) => Promise<void>;
  isSubmitting: boolean;
};

export function MappingStep({
  headers,
  initialMapping,
  onBack,
  onSubmit,
  isSubmitting,
}: MappingStepProps) {
  const [mapping, setMapping] = useState<ColumnMapping>(initialMapping);
  const [error, setError] = useState<string | null>(null);
  const [templateSaved, setTemplateSaved] = useState(false);

  const emailMapped = Object.values(mapping).includes("email");

  function setField(column: string, value: FieldMapping) {
    setMapping((prev) => {
      const next = { ...prev };
      if (
        value !== "skip" &&
        value !== "pref:newsletter" &&
        value !== "pref:product_updates" &&
        value !== "pref:marketing"
      ) {
        for (const [k, v] of Object.entries(next)) {
          if (v === value && k !== column) {
            next[k] = "skip";
          }
        }
      }
      next[column] = value;
      return next;
    });
    setError(null);
  }

  function handleLoadTemplate() {
    const template = loadTemplate();
    if (!template) return;
    setMapping((prev) => {
      const next = { ...prev };
      for (const [col, field] of Object.entries(template)) {
        if (col in next) next[col] = field;
      }
      return next;
    });
  }

  function handleSaveTemplate() {
    saveTemplate(mapping);
    setTemplateSaved(true);
    setTimeout(() => setTemplateSaved(false), 2000);
  }

  async function handleSubmit() {
    if (!emailMapped) {
      setError("Map at least one column to Email before continuing.");
      return;
    }
    await onSubmit(mapping);
  }

  return (
    <div className="grid gap-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm text-text-muted">
          Map each CSV column to a contact field. Unmapped columns are ignored.
        </p>
        <div className="flex gap-2">
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={handleLoadTemplate}
          >
            Load saved template
          </Button>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={handleSaveTemplate}
          >
            {templateSaved ? "Saved!" : "Save as template"}
          </Button>
        </div>
      </div>

      <div className="surface-panel overflow-hidden">
        <table className="w-full text-sm" aria-label="Column mapping">
          <thead>
            <tr className="border-b border-border">
              <th className="px-4 py-3 text-left font-medium text-text-muted">
                CSV column
              </th>
              <th className="px-4 py-3 text-left font-medium text-text-muted">
                Maps to
              </th>
            </tr>
          </thead>
          <tbody>
            {headers.map((header) => (
              <tr key={header} className="border-b border-border last:border-0">
                <td className="px-4 py-3 font-medium">{header}</td>
                <td className="px-4 py-3">
                  <select
                    className="field h-9 w-full max-w-xs"
                    aria-label={`Map column "${header}"`}
                    value={mapping[header] ?? "skip"}
                    onChange={(e) =>
                      setField(header, e.target.value as FieldMapping)
                    }
                  >
                    {KNOWN_FIELDS.map((f) => (
                      <option key={f.value} value={f.value}>
                        {f.label}
                      </option>
                    ))}
                  </select>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {!emailMapped ? (
        <p className="text-sm text-text-muted">
          At least one column must be mapped to{" "}
          <strong>Email (required)</strong> to continue.
        </p>
      ) : null}

      {error ? (
        <p role="alert" className="text-sm text-danger">
          {error}
        </p>
      ) : null}

      <div className="flex justify-between gap-3">
        <Button type="button" variant="outline" onClick={onBack}>
          Back
        </Button>
        <Button
          type="button"
          disabled={!emailMapped || isSubmitting}
          onClick={() => void handleSubmit()}
        >
          {isSubmitting ? "Uploading…" : "Upload and start import"}
        </Button>
      </div>
    </div>
  );
}
