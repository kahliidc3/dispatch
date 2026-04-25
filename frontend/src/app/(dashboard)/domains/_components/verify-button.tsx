"use client";

import { useEffect, useState } from "react";
import { RefreshCw } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { clientJson } from "@/lib/api/client";
import { apiEndpoints } from "@/lib/api/endpoints";
import { cn } from "@/lib/utils";
import type { DomainStatus } from "@/types/domain";

const POLL_INTERVAL_MS = 5_000;
const POLL_TIMEOUT_MS = 5 * 60 * 1_000;

type VerifyButtonProps = {
  domainId: string;
  initialStatus: DomainStatus;
};

export function VerifyButton({ domainId, initialStatus }: VerifyButtonProps) {
  const [status, setStatus] = useState<DomainStatus>(initialStatus);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const isVerifying = status === "verifying";
  const canVerify = status === "pending" || status === "verifying";

  useEffect(() => {
    if (!isVerifying) return;

    const startedAt = Date.now();
    let cancelled = false;
    let timeoutId: ReturnType<typeof setTimeout> | null = null;

    function scheduleNextPoll() {
      if (cancelled) return;

      const elapsed = Date.now() - startedAt;

      if (elapsed >= POLL_TIMEOUT_MS) {
        toast.error(
          "Verification timed out. DNS propagation can take up to 48 hours.",
        );
        return;
      }

      timeoutId = setTimeout(async () => {
        if (cancelled) return;

        try {
          const domain = await clientJson<{ status: DomainStatus }>(
            apiEndpoints.domains.byId(domainId),
            { redirectOnUnauthorized: true },
          );

          if (!cancelled) {
            setStatus(domain.status);
            if (domain.status === "verifying") {
              scheduleNextPoll();
            } else if (domain.status === "verified") {
              toast.success("Domain verified successfully.");
            }
          }
        } catch {
          if (!cancelled) scheduleNextPoll();
        }
      }, POLL_INTERVAL_MS);
    }

    scheduleNextPoll();

    return () => {
      cancelled = true;
      if (timeoutId !== null) clearTimeout(timeoutId);
    };
  }, [isVerifying, domainId]);

  async function handleVerify() {
    setIsSubmitting(true);

    try {
      await clientJson(apiEndpoints.domains.verify(domainId), {
        method: "POST",
        redirectOnUnauthorized: true,
      });
      setStatus("verifying");
      toast.info("Verification started. Polling DNS records every 5 seconds…");
    } catch {
      toast.error("Could not start verification. Try again in a moment.");
    } finally {
      setIsSubmitting(false);
    }
  }

  if (!canVerify) return null;

  return (
    <Button
      type="button"
      variant={isVerifying ? "outline" : "default"}
      disabled={isSubmitting || isVerifying}
      onClick={() => void handleVerify()}
      aria-label={isVerifying ? "DNS verification in progress" : "Verify DNS records"}
    >
      <RefreshCw
        className={cn("h-4 w-4", isVerifying && "animate-spin")}
        aria-hidden
      />
      {isVerifying ? "Verifying…" : "Verify DNS"}
    </Button>
  );
}
