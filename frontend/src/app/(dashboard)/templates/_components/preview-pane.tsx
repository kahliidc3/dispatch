"use client";

import { useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";

const DEFAULT_SAMPLE = JSON.stringify(
  {
    first_name: "Avery",
    last_name: "Chen",
    email: "avery@example.com",
    sender_name: "The Team",
    unsubscribe_url: "https://example.com/unsubscribe?t=sample",
  },
  null,
  2,
);

function applyMergeTags(
  template: string,
  sample: Record<string, string>,
): string {
  return template.replace(/\{\{(\w+)\}\}/g, (_, key: string) => {
    return sample[key] ?? `{{${key}}}`;
  });
}

type PreviewPaneProps = {
  subject: string;
  bodyHtml: string;
  bodyText: string;
};

export function PreviewPane({ subject, bodyHtml, bodyText }: PreviewPaneProps) {
  const [sampleJson, setSampleJson] = useState(DEFAULT_SAMPLE);
  const [jsonError, setJsonError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<"html" | "text">("html");
  const iframeRef = useRef<HTMLIFrameElement>(null);

  const sample = (() => {
    try {
      const parsed = JSON.parse(sampleJson) as Record<string, string>;
      setJsonError(null);
      return parsed;
    } catch {
      return null;
    }
  })();

  const renderedSubject = sample ? applyMergeTags(subject, sample) : subject;
  const renderedHtml = sample ? applyMergeTags(bodyHtml, sample) : bodyHtml;
  const renderedText = sample ? applyMergeTags(bodyText, sample) : bodyText;

  useEffect(() => {
    const iframe = iframeRef.current;
    if (!iframe || viewMode !== "html") return;
    const doc = iframe.contentDocument;
    if (!doc) return;
    doc.open();
    doc.write(
      `<!DOCTYPE html><html><head><meta charset="utf-8"><style>body{font-family:sans-serif;font-size:14px;line-height:1.6;padding:16px;margin:0;color:#111}</style></head><body>${renderedHtml}</body></html>`,
    );
    doc.close();
  }, [renderedHtml, viewMode]);

  function handleJsonChange(value: string) {
    setSampleJson(value);
    try {
      JSON.parse(value);
      setJsonError(null);
    } catch {
      setJsonError("Invalid JSON");
    }
  }

  return (
    <section className="surface-panel p-6 grid gap-5">
      <div className="flex items-center justify-between gap-3">
        <h2 className="section-title">Preview</h2>
        <div className="flex gap-2">
          <Button
            type="button"
            variant={viewMode === "html" ? "default" : "outline"}
            size="sm"
            onClick={() => setViewMode("html")}
          >
            HTML
          </Button>
          <Button
            type="button"
            variant={viewMode === "text" ? "default" : "outline"}
            size="sm"
            onClick={() => setViewMode("text")}
          >
            Plain text
          </Button>
        </div>
      </div>

      {renderedSubject ? (
        <div className="surface-panel-muted rounded-lg px-4 py-2 text-sm">
          <span className="text-text-muted">Subject: </span>
          <span className="font-medium">{renderedSubject}</span>
        </div>
      ) : null}

      <div className="overflow-hidden rounded-lg border border-border bg-white dark:bg-surface-muted min-h-48">
        {viewMode === "html" ? (
          <iframe
            ref={iframeRef}
            title="Email HTML preview"
            sandbox="allow-same-origin"
            className="w-full min-h-48 h-full border-0"
            aria-label="HTML email preview"
          />
        ) : (
          <pre className="mono text-xs p-4 whitespace-pre-wrap leading-5 text-foreground">
            {renderedText || <span className="text-text-muted">No body text</span>}
          </pre>
        )}
      </div>

      <div>
        <div className="flex items-center justify-between gap-3 mb-2">
          <label className="label" htmlFor="sample-json">
            Sample contact data
          </label>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => {
              setSampleJson(DEFAULT_SAMPLE);
              setJsonError(null);
            }}
          >
            Reset
          </Button>
        </div>
        <textarea
          id="sample-json"
          className="field mono text-xs min-h-32 resize-y"
          value={sampleJson}
          onChange={(e) => handleJsonChange(e.target.value)}
          spellCheck={false}
          aria-describedby={jsonError ? "sample-json-error" : undefined}
        />
        {jsonError ? (
          <p id="sample-json-error" role="alert" className="mt-1 text-xs text-danger">
            {jsonError}
          </p>
        ) : null}
      </div>
    </section>
  );
}
