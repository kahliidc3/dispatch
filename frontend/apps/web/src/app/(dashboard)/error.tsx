"use client";

import { useEffect } from "react";
import { Button } from "@/components/ui/button";
import { trackError } from "@/lib/telemetry";

type DashboardErrorProps = {
  error: Error;
  reset: () => void;
};

export default function DashboardError({
  error,
  reset,
}: DashboardErrorProps) {
  useEffect(() => {
    void trackError(error, {
      boundary: "dashboard",
    });
  }, [error]);

  return (
    <div className="surface-panel p-6">
      <div className="page-stack">
        <div>
          <h1 className="page-title">Dashboard route error</h1>
          <p className="page-description">
            This route failed during render. Reset it to continue working inside
            the protected shell.
          </p>
        </div>
        <div className="surface-panel-muted p-4">
          <p className="mono text-sm text-text-muted">{error.message}</p>
        </div>
        <div>
          <Button type="button" onClick={reset}>
            Retry
          </Button>
        </div>
      </div>
    </div>
  );
}
