"use client";

import Link from "next/link";
import { useState } from "react";
import { Plus } from "lucide-react";
import { toast } from "sonner";
import { ConfirmDialog } from "@/components/shared/confirm-dialog";
import { DataTable } from "@/components/shared/data-table";
import { EmptyState } from "@/components/shared/empty-state";
import { SectionPanel } from "@/components/patterns/section-panel";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
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
import { Input } from "@/components/ui/input";
import { clientJson } from "@/lib/api/client";
import { apiEndpoints } from "@/lib/api/endpoints";
import { formatTimestamp } from "@/lib/formatters";
import type { DomainListItem, SenderProfile } from "@/types/domain";

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

type CreateFormState = {
  name: string;
  fromName: string;
  fromEmail: string;
  replyTo: string;
  domainId: string;
  error: string | null;
};

const emptyForm: CreateFormState = {
  name: "",
  fromName: "",
  fromEmail: "",
  replyTo: "",
  domainId: "",
  error: null,
};

type SenderProfilesManagerProps = {
  initialProfiles: SenderProfile[];
  verifiedDomains: DomainListItem[];
};

export function SenderProfilesManager({
  initialProfiles,
  verifiedDomains,
}: SenderProfilesManagerProps) {
  const [profiles, setProfiles] = useState(initialProfiles);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState<CreateFormState>(emptyForm);
  const [isPending, setIsPending] = useState(false);

  function setField<K extends keyof CreateFormState>(
    key: K,
    value: CreateFormState[K],
  ) {
    setForm((prev) => ({ ...prev, [key]: value, error: null }));
  }

  function validate(): string | null {
    if (!form.name.trim()) return "Give this profile a short descriptive name.";
    if (!form.fromName.trim()) return "Enter the display name shown to recipients.";
    if (!EMAIL_RE.test(form.fromEmail.trim())) return "Enter a valid from address on a verified domain.";
    if (!form.domainId) return "Select a verified domain to send from.";

    const domain = verifiedDomains.find((d) => d.id === form.domainId);

    if (domain && !form.fromEmail.trim().endsWith(`@${domain.name}`)) {
      return `From address must use the selected domain (@${domain.name}).`;
    }

    return null;
  }

  async function handleCreate() {
    const validationError = validate();

    if (validationError) {
      setForm((prev) => ({ ...prev, error: validationError }));
      return;
    }

    setIsPending(true);

    try {
      const profile = await clientJson<SenderProfile>(
        apiEndpoints.senderProfiles.create,
        {
          method: "POST",
          body: {
            name: form.name.trim(),
            fromName: form.fromName.trim(),
            fromEmail: form.fromEmail.trim(),
            replyTo: form.replyTo.trim() || null,
            domainId: form.domainId,
          },
        },
      );
      setProfiles((prev) => [profile, ...prev]);
      toast.success("Sender profile created.");
      setOpen(false);
      setForm(emptyForm);
    } catch {
      toast.error("Could not create profile. Check the values and try again.");
    } finally {
      setIsPending(false);
    }
  }

  async function handleDelete(id: string) {
    await clientJson(apiEndpoints.senderProfiles.delete(id), {
      method: "DELETE",
      redirectOnUnauthorized: true,
    });
    setProfiles((prev) => prev.filter((p) => p.id !== id));
    toast.success("Sender profile deleted.");
  }

  const createDialog = (
    <Dialog
      open={open}
      onOpenChange={(next) => {
        setOpen(next);
        if (!next) setForm(emptyForm);
      }}
    >
      <DialogTrigger asChild>
        <Button type="button" disabled={verifiedDomains.length === 0}>
          <Plus className="h-4 w-4" />
          Create profile
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Create sender profile</DialogTitle>
          <DialogDescription>
            A sender profile defines the from address and display name used in
            email headers. Only verified domains are eligible.
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4">
          <div>
            <label className="label" htmlFor="sp-name">
              Profile name
            </label>
            <Input
              id="sp-name"
              placeholder="Campaign broadcast"
              value={form.name}
              onChange={(e) => setField("name", e.target.value)}
            />
          </div>
          <div>
            <label className="label" htmlFor="sp-domain">
              Sending domain
            </label>
            <select
              id="sp-domain"
              className="field"
              value={form.domainId}
              onChange={(e) => setField("domainId", e.target.value)}
            >
              <option value="">Select a verified domain…</option>
              {verifiedDomains.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="label" htmlFor="sp-from-name">
              Display name
            </label>
            <Input
              id="sp-from-name"
              placeholder="Dispatch Platform"
              value={form.fromName}
              onChange={(e) => setField("fromName", e.target.value)}
            />
          </div>
          <div>
            <label className="label" htmlFor="sp-from-email">
              From address
            </label>
            <Input
              id="sp-from-email"
              type="email"
              inputMode="email"
              placeholder={
                form.domainId
                  ? `noreply@${verifiedDomains.find((d) => d.id === form.domainId)?.name ?? "example.com"}`
                  : "noreply@yourdomain.com"
              }
              value={form.fromEmail}
              onChange={(e) => setField("fromEmail", e.target.value)}
            />
          </div>
          <div>
            <label className="label" htmlFor="sp-reply-to">
              Reply-To{" "}
              <span className="text-text-muted font-normal">(optional)</span>
            </label>
            <Input
              id="sp-reply-to"
              type="email"
              inputMode="email"
              placeholder="support@yourdomain.com"
              value={form.replyTo}
              onChange={(e) => setField("replyTo", e.target.value)}
            />
          </div>
          {form.error ? (
            <p className="text-sm text-danger">{form.error}</p>
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
            onClick={() => void handleCreate()}
          >
            {isPending ? "Creating…" : "Create profile"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );

  return (
    <SectionPanel
      title="Sender profiles"
      description="Each profile ties a from address to a verified sending domain. Unverified domains are blocked at both the UI and API level."
      actions={createDialog}
    >
      {verifiedDomains.length === 0 ? (
        <p className="text-sm text-text-muted">
          No verified domains available.{" "}
          <Link href="/domains" className="underline hover:no-underline">
            Add and verify a domain
          </Link>{" "}
          before creating sender profiles.
        </p>
      ) : null}

      {profiles.length === 0 ? (
        <EmptyState
          title="No sender profiles"
          description="Create a profile to define the from address used in outgoing campaigns."
        />
      ) : (
        <DataTable
          caption="Sender profile inventory"
          columns={[
            { key: "name", label: "Name" },
            { key: "from", label: "From" },
            { key: "domain", label: "Domain" },
            { key: "status", label: "Status" },
            { key: "createdAt", label: "Created" },
            { key: "actions", label: "Actions" },
          ]}
          rows={profiles.map((profile) => ({
            name: (
              <Link
                href={`/sender-profiles/${profile.id}`}
                className="font-medium hover:underline"
              >
                {profile.name}
              </Link>
            ),
            from: (
              <span className="text-sm">
                <span className="font-medium">{profile.fromName}</span>
                <span className="ml-1 text-text-muted">&lt;{profile.fromEmail}&gt;</span>
              </span>
            ),
            domain: (
              <Link
                href={`/domains/${profile.domainId}`}
                className="text-sm hover:underline"
              >
                {profile.domainName}
              </Link>
            ),
            status: (
              <Badge variant={profile.status === "active" ? "success" : "outline"}>
                {profile.status}
              </Badge>
            ),
            createdAt: (
              <span className="text-sm text-text-muted">
                {formatTimestamp(profile.createdAt)}
              </span>
            ),
            actions: (
              <ConfirmDialog
                title="Delete sender profile"
                description={`Deleting "${profile.name}" will prevent it from being used in new campaigns. Existing campaign runs are not affected.`}
                confirmLabel="Delete profile"
                trigger={
                  <Button type="button" variant="outline" size="sm">
                    Delete
                  </Button>
                }
                onConfirm={() => handleDelete(profile.id)}
              />
            ),
          }))}
        />
      )}
    </SectionPanel>
  );
}
