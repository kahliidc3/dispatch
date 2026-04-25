"use client";

import { useState } from "react";
import { Plus } from "lucide-react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
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
import type { DomainListItem } from "@/types/domain";

const HOSTNAME_RE = /^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}$/i;

type AddDomainDialogProps = {
  onAdded?: (domain: DomainListItem) => void;
};

export function AddDomainDialog({ onAdded }: AddDomainDialogProps) {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isPending, setIsPending] = useState(false);

  function reset() {
    setName("");
    setError(null);
  }

  async function handleCreate() {
    const trimmed = name.trim();

    if (!trimmed) {
      setError("Enter the fully-qualified domain name to send from.");
      return;
    }

    if (!HOSTNAME_RE.test(trimmed)) {
      setError("Enter a valid domain name, e.g. mail.example.com.");
      return;
    }

    setIsPending(true);

    try {
      const domain = await clientJson<DomainListItem>(
        apiEndpoints.domains.create,
        { method: "POST", body: { name: trimmed } },
      );
      toast.success("Domain added. Set up the DNS records to start verification.");
      onAdded?.(domain);
      setOpen(false);
      reset();
      router.push(`/domains/${domain.id}`);
    } catch {
      toast.error("Could not add domain. Check the name and try again.");
    } finally {
      setIsPending(false);
    }
  }

  return (
    <Dialog
      open={open}
      onOpenChange={(next) => {
        setOpen(next);
        if (!next) reset();
      }}
    >
      <DialogTrigger asChild>
        <Button type="button">
          <Plus className="h-4 w-4" />
          Add domain
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Add sending domain</DialogTitle>
          <DialogDescription>
            Enter the domain you want to send from. DNS records will be
            generated for you to add to your DNS provider.
          </DialogDescription>
        </DialogHeader>
        <div>
          <label className="label" htmlFor="add-domain-name">
            Domain name
          </label>
          <Input
            id="add-domain-name"
            type="text"
            inputMode="url"
            placeholder="mail.example.com"
            value={name}
            autoComplete="off"
            spellCheck={false}
            onChange={(e) => {
              setName(e.target.value);
              setError(null);
            }}
            onKeyDown={(e) => {
              if (e.key === "Enter") void handleCreate();
            }}
          />
          {error ? (
            <p className="mt-2 text-sm text-danger">{error}</p>
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
            {isPending ? "Adding…" : "Add domain"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
