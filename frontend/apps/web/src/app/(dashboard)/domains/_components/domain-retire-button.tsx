"use client";

import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { ConfirmDialog } from "@/components/shared/confirm-dialog";
import { Button } from "@/components/ui/button";
import { clientJson } from "@/lib/api/client";
import { apiEndpoints } from "@/lib/api/endpoints";
import type { DomainStatus } from "@/types/domain";

type DomainRetireButtonProps = {
  domainId: string;
  status: DomainStatus;
};

export function DomainRetireButton({
  domainId,
  status,
}: DomainRetireButtonProps) {
  const router = useRouter();

  if (status === "retired" || status === "burnt") return null;

  async function handleRetire({ reason }: { reason: string }) {
    await clientJson(apiEndpoints.domains.retire(domainId), {
      method: "POST",
      body: { reason },
      redirectOnUnauthorized: true,
    });
    toast.success("Domain retired. No further sends will use this domain.");
    router.refresh();
  }

  return (
    <ConfirmDialog
      title="Retire domain"
      description="Retiring a domain permanently stops all sending from it. This action cannot be undone."
      confirmLabel="Retire domain"
      requireReason
      reasonLabel="Reason"
      reasonPlaceholder="e.g. Replaced by new domain, no longer in use"
      trigger={
        <Button type="button" variant="outline">
          Retire domain
        </Button>
      }
      onConfirm={handleRetire}
    />
  );
}
