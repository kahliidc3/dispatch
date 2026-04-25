"use client";

import { useState } from "react";
import { useSearchParams } from "next/navigation";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { clientJson } from "@/lib/api/client";
import { apiEndpoints } from "@/lib/api/endpoints";

export function UnsubscribeForm() {
  const searchParams = useSearchParams();
  const token = searchParams.get("t");
  const [confirmed, setConfirmed] = useState(false);
  const [isPending, setIsPending] = useState(false);

  if (!token) {
    return (
      <div className="surface-panel p-8 text-center">
        <p className="text-sm text-text-muted">
          This unsubscribe link is invalid or has expired. If you believe this
          is a mistake, contact support.
        </p>
      </div>
    );
  }

  if (confirmed) {
    return (
      <div className="surface-panel p-8 text-center">
        <h2 className="mb-3 text-lg font-semibold">You&apos;ve been unsubscribed</h2>
        <p className="text-sm text-text-muted">
          You won&apos;t receive any further emails from us. If you changed your
          mind, contact support to resubscribe.
        </p>
      </div>
    );
  }

  async function handleConfirm() {
    setIsPending(true);
    try {
      await clientJson(apiEndpoints.publicUnsubscribe.confirm, {
        method: "POST",
        body: { token },
      });
      setConfirmed(true);
    } catch {
      toast.error(
        "Could not process your request. The link may have already been used.",
      );
    } finally {
      setIsPending(false);
    }
  }

  return (
    <div className="surface-panel p-8">
      <h2 className="mb-3 text-lg font-semibold">Confirm unsubscribe</h2>
      <p className="mb-6 text-sm text-text-muted">
        Click the button below to confirm that you no longer want to receive
        emails from us. This action cannot be undone from this page.
      </p>
      <Button
        type="button"
        disabled={isPending}
        onClick={() => void handleConfirm()}
      >
        {isPending ? "Processing…" : "Unsubscribe"}
      </Button>
    </div>
  );
}
