"use client";

import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { ConfirmDialog } from "@/components/shared/confirm-dialog";
import { clientJson } from "@/lib/api/client";
import { apiEndpoints } from "@/lib/api/endpoints";

type DeleteContactButtonProps = {
  contactId: string;
  email: string;
};

export function DeleteContactButton({ contactId, email }: DeleteContactButtonProps) {
  const router = useRouter();

  async function handleDelete({ reason }: { reason: string }) {
    await clientJson(apiEndpoints.contacts.delete(contactId), {
      method: "DELETE",
      body: { reason },
    });
    toast.success("Contact deleted.");
    router.push("/contacts");
  }

  return (
    <ConfirmDialog
      title="Delete contact"
      description={`Permanently delete ${email}? This removes all associated history and cannot be undone.`}
      triggerLabel="Delete contact"
      confirmLabel="Delete"
      requireReason
      reasonLabel="Reason"
      reasonPlaceholder="Why is this contact being deleted?"
      onConfirm={handleDelete}
    />
  );
}
