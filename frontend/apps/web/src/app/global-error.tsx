"use client";

import { useEffect } from "react";
import { Button } from "@/components/ui/button";
import { trackError } from "@/lib/telemetry";

type GlobalErrorProps = {
  error: Error & { digest?: string };
  reset: () => void;
};

export default function GlobalError({ error, reset }: GlobalErrorProps) {
  useEffect(() => {
    void trackError(error, {
      boundary: "global",
      digest: error.digest ?? null,
    });
  }, [error]);

  return (
    <html lang="en">
      <body>
        <main className="flex min-h-screen items-center justify-center px-6 py-12">
          <div className="surface-panel w-full max-w-2xl p-8">
            <div className="page-stack">
              <header>
                <h1 className="page-title">Application error</h1>
                <p className="page-description">
                  A rendering error interrupted this route. The shell is still
                  intact, and this error has been prepared for telemetry with
                  PII redaction.
                </p>
              </header>
              <div className="surface-panel-muted p-4">
                <p className="text-sm font-medium">Error message</p>
                <p className="mono mt-2 text-sm text-[color:var(--text-muted)]">
                  {error.message}
                </p>
                {error.digest ? (
                  <p className="mono mt-2 text-xs text-text-muted">
                    digest: {error.digest}
                  </p>
                ) : null}
              </div>
              <div className="flex flex-wrap gap-3">
                <Button type="button" onClick={reset}>
                  Retry
                </Button>
              </div>
            </div>
          </div>
        </main>
      </body>
    </html>
  );
}
