"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { SectionPanel } from "@/components/patterns/section-panel";
import { ConfirmDialog } from "@/components/shared/confirm-dialog";
import { DataTable } from "@/components/shared/data-table";
import { clientJson } from "@/lib/api/client";
import { apiEndpoints } from "@/lib/api/endpoints";
import { formatTimestamp } from "@/lib/formatters";
import type { ListMember } from "@/types/list";

type ListMembersPanelProps = {
  listId: string;
  listName: string;
  initialMembers: ListMember[];
};

export function ListMembersPanel({
  listId,
  listName,
  initialMembers,
}: ListMembersPanelProps) {
  const router = useRouter();
  const [members, setMembers] = useState(initialMembers);
  const [addOpen, setAddOpen] = useState(false);
  const [contactId, setContactId] = useState("");
  const [addError, setAddError] = useState<string | null>(null);
  const [isPending, setIsPending] = useState(false);

  async function handleAddMember() {
    const trimmed = contactId.trim();
    if (!trimmed) {
      setAddError("Contact ID is required.");
      return;
    }
    setIsPending(true);
    try {
      const member = await clientJson<ListMember>(
        apiEndpoints.lists.addMember(listId),
        { method: "POST", body: { contactId: trimmed } },
      );
      toast.success("Member added.");
      setMembers((prev) => [...prev, member]);
      setAddOpen(false);
      setContactId("");
      router.refresh();
    } catch {
      setAddError("Could not add member. Check the contact ID and try again.");
    } finally {
      setIsPending(false);
    }
  }

  async function handleRemoveMember(cId: string) {
    await clientJson(apiEndpoints.lists.removeMember(listId, cId), {
      method: "DELETE",
    });
    toast.success("Member removed.");
    setMembers((prev) => prev.filter((m) => m.contactId !== cId));
    router.refresh();
  }

  return (
    <SectionPanel
      title="Members"
      description={`${members.length} contact(s) in this list`}
      actions={
        <Dialog
          open={addOpen}
          onOpenChange={(o) => {
            setAddOpen(o);
            if (!o) {
              setContactId("");
              setAddError(null);
            }
          }}
        >
          <DialogTrigger asChild>
            <Button type="button">Add member</Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Add member</DialogTitle>
              <DialogDescription>
                Enter the contact ID to add to {listName}.
              </DialogDescription>
            </DialogHeader>
            <div>
              <label className="label" htmlFor="add-member-id">
                Contact ID
              </label>
              <Input
                id="add-member-id"
                type="text"
                placeholder="ctc-001"
                value={contactId}
                onChange={(e) => {
                  setContactId(e.target.value);
                  setAddError(null);
                }}
                onKeyDown={(e) => {
                  if (e.key === "Enter") void handleAddMember();
                }}
              />
              {addError ? (
                <p className="mt-2 text-sm text-danger">{addError}</p>
              ) : null}
            </div>
            <DialogFooter>
              <DialogClose asChild>
                <Button type="button" variant="outline">
                  Cancel
                </Button>
              </DialogClose>
              <Button
                type="button"
                disabled={isPending}
                onClick={() => void handleAddMember()}
              >
                {isPending ? "Adding…" : "Add member"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      }
    >
      {members.length > 0 ? (
        <DataTable
          columns={[
            { key: "email", label: "Email" },
            { key: "contactId", label: "Contact ID" },
            { key: "addedAt", label: "Added", className: "text-right" },
            { key: "actions", label: "", className: "text-right" },
          ]}
          rows={members.map((m) => ({
            email: (
              <Link
                href={`/contacts/${m.contactId}`}
                className="font-medium hover:underline"
              >
                {m.email}
              </Link>
            ),
            contactId: (
              <span className="mono text-sm text-text-muted">
                {m.contactId}
              </span>
            ),
            addedAt: formatTimestamp(m.addedAt),
            actions: (
              <ConfirmDialog
                title="Remove member"
                description={`Remove ${m.email} from ${listName}? The contact is not deleted.`}
                trigger={
                  <Button type="button" variant="outline" size="sm">
                    Remove
                  </Button>
                }
                confirmLabel="Remove"
                onConfirm={() => handleRemoveMember(m.contactId)}
              />
            ),
          }))}
        />
      ) : (
        <p className="py-4 text-sm text-text-muted">
          No members yet. Add contacts to this list to get started.
        </p>
      )}
    </SectionPanel>
  );
}
