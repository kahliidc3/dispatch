"use client";

import { Button } from "@/components/ui/button";

type GlobalErrorProps = {
  error: Error & { digest?: string };
  reset: () => void;
};

export default function GlobalError({ error, reset }: GlobalErrorProps) {
  return (
    <html lang="en">
      <body>
        <main className="flex min-h-screen items-center justify-center px-6 py-12">
          <div className="surface-panel w-full max-w-2xl p-8">
            <div className="page-stack">
              <header>
                <h1 className="page-title">Application error</h1>
                <p className="page-description">
                  A rendering error interrupted this view. The scaffold is still
                  intact, but this route needs a reset.
                </p>
              </header>
              <div className="surface-panel-muted p-4">
                <p className="text-sm font-medium">Error message</p>
                <p className="mono mt-2 text-sm text-[color:var(--text-muted)]">
                  {error.message}
                </p>
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
