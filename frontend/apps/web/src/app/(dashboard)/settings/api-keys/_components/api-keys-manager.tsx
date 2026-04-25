"use client";

import { useMemo, useState } from "react";
import { Copy, Plus } from "lucide-react";
import { toast } from "sonner";
import { ConfirmDialog } from "@/components/shared/confirm-dialog";
import { DataTable } from "@/components/shared/data-table";
import { SectionPanel } from "@/components/patterns/section-panel";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  DialogClose,
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { formatTimestamp } from "@/lib/formatters";
import type { ApiKeyRecord } from "@/types/api";

type ManagedApiKey = ApiKeyRecord & {
  revokedReason?: string | null;
};

type ApiKeysManagerProps = {
  initialKeys: ManagedApiKey[];
};

type DraftState = {
  name: string;
  error: string | null;
};

function createSecretPart(length: number) {
  const alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789";

  return Array.from({ length }, () =>
    alphabet[Math.floor(Math.random() * alphabet.length)],
  ).join("");
}

function createApiKeyMaterial() {
  const prefixSeed = createSecretPart(6).toLowerCase();
  const secretSeed = createSecretPart(24);

  return {
    prefix: `ak_live_${prefixSeed}`,
    plaintext: `ak_live_${prefixSeed}_${secretSeed}`,
    last4: secretSeed.slice(-4),
  };
}

export function ApiKeysManager({ initialKeys }: ApiKeysManagerProps) {
  const [keys, setKeys] = useState(initialKeys);
  const [open, setOpen] = useState(false);
  const [draft, setDraft] = useState<DraftState>({
    name: "",
    error: null,
  });
  const [revealedSecret, setRevealedSecret] = useState<string | null>(null);

  const activeKeys = useMemo(
    () => keys.filter((key) => key.status === "active").length,
    [keys],
  );

  function resetCreateDialog() {
    setDraft({
      name: "",
      error: null,
    });
    setRevealedSecret(null);
  }

  function handleCreate() {
    const name = draft.name.trim();

    if (name.length < 3) {
      setDraft((current) => ({
        ...current,
        error: "Give this key a short operator-facing name.",
      }));
      return;
    }

    const material = createApiKeyMaterial();
    const now = new Date().toISOString();
    const nextKey: ManagedApiKey = {
      id: crypto.randomUUID(),
      name,
      prefix: material.prefix,
      last4: material.last4,
      createdAt: now,
      lastUsedAt: null,
      revokedAt: null,
      status: "active",
      revokedReason: null,
    };

    setKeys((current) => [nextKey, ...current]);
    setRevealedSecret(material.plaintext);
    setDraft({
      name,
      error: null,
    });
  }

  async function handleCopySecret() {
    if (!revealedSecret) {
      return;
    }

    await navigator.clipboard.writeText(revealedSecret);
    toast.success("API key copied to the clipboard.");
  }

  function handleRevoke(id: string, reason: string) {
    setKeys((current) =>
      current.map((key) =>
        key.id === id
          ? {
              ...key,
              status: "revoked",
              revokedAt: new Date().toISOString(),
              revokedReason: reason,
            }
          : key,
      ),
    );

    toast.success("API key revoked.");
  }

  return (
    <SectionPanel
      title="Integration credentials"
      description="Create operator API keys, reveal the plaintext secret once, and revoke compromised credentials with an audit reason."
      actions={
        <Dialog
          open={open}
          onOpenChange={(nextOpen) => {
            setOpen(nextOpen);

            if (!nextOpen) {
              resetCreateDialog();
            }
          }}
        >
          <DialogTrigger asChild>
            <Button type="button">
              <Plus className="h-4 w-4" />
              Create key
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>
                {revealedSecret ? "Store the new key now" : "Create API key"}
              </DialogTitle>
              <DialogDescription>
                {revealedSecret
                  ? "This secret is shown once. Closing the dialog clears it from memory."
                  : "Use a descriptive name so operators can revoke the right credential quickly."}
              </DialogDescription>
            </DialogHeader>
            {revealedSecret ? (
              <div className="grid gap-4">
                <div className="surface-panel-muted grid gap-2 p-4">
                  <span className="text-sm text-text-muted">Plaintext key</span>
                  <code className="mono overflow-x-auto text-sm text-foreground">
                    {revealedSecret}
                  </code>
                </div>
                <p className="text-sm text-text-muted">
                  Copy the secret into a secure store before closing. The table
                  below keeps only the public prefix and the last four
                  characters.
                </p>
              </div>
            ) : (
              <div>
                <label className="label" htmlFor="api-key-name">
                  Key name
                </label>
                <Input
                  id="api-key-name"
                  value={draft.name}
                  placeholder="Campaign import worker"
                  onChange={(event) =>
                    setDraft({
                      name: event.target.value,
                      error: null,
                    })
                  }
                />
                {draft.error ? (
                  <p className="mt-2 text-sm text-danger">{draft.error}</p>
                ) : null}
              </div>
            )}
            <DialogFooter>
              {revealedSecret ? (
                <>
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => void handleCopySecret()}
                  >
                    <Copy className="h-4 w-4" />
                    Copy secret
                  </Button>
                  <DialogClose asChild>
                    <Button
                      type="button"
                      onClick={() => {
                        resetCreateDialog();
                      }}
                    >
                      Close and clear
                    </Button>
                  </DialogClose>
                </>
              ) : (
                <>
                  <DialogClose asChild>
                    <Button type="button" variant="outline">
                      Cancel
                    </Button>
                  </DialogClose>
                  <Button type="button" onClick={handleCreate}>
                    Create key
                  </Button>
                </>
              )}
            </DialogFooter>
          </DialogContent>
        </Dialog>
      }
    >
      <div className="grid gap-4 md:grid-cols-3">
        <div className="surface-panel-muted p-4">
          <p className="text-sm text-text-muted">Active keys</p>
          <p className="mt-1 text-2xl font-semibold">{activeKeys}</p>
        </div>
        <div className="surface-panel-muted p-4">
          <p className="text-sm text-text-muted">Revoked keys</p>
          <p className="mt-1 text-2xl font-semibold">{keys.length - activeKeys}</p>
        </div>
        <div className="surface-panel-muted p-4">
          <p className="text-sm text-text-muted">Reveal policy</p>
          <p className="mt-1 text-sm leading-6 text-foreground">
            Plaintext secrets are rendered once, never stored, and cleared when
            the modal closes.
          </p>
        </div>
      </div>
      <DataTable
        caption="API key inventory"
        columns={[
          { key: "name", label: "Name" },
          { key: "token", label: "Token", className: "mono text-xs" },
          { key: "createdAt", label: "Created" },
          { key: "lastUsedAt", label: "Last used" },
          { key: "revokedAt", label: "Revoked" },
          { key: "status", label: "Status" },
          { key: "actions", label: "Actions" },
        ]}
        rows={keys.map((key) => ({
          name: key.name,
          token: `${key.prefix}••••${key.last4}`,
          createdAt: formatTimestamp(key.createdAt),
          lastUsedAt: key.lastUsedAt ? formatTimestamp(key.lastUsedAt) : "Never",
          revokedAt: key.revokedAt ? formatTimestamp(key.revokedAt) : "Active",
          status: (
            <Badge variant={key.status === "active" ? "success" : "outline"}>
              {key.status}
            </Badge>
          ),
          actions:
            key.status === "active" ? (
              <ConfirmDialog
                title="Revoke API key"
                description="Revoking this key blocks any integration still using the secret. Add the reason for the audit trail."
                confirmLabel="Revoke key"
                requireReason
                reasonLabel="Revocation reason"
                reasonPlaceholder="Compromised, rotated, or no longer needed"
                trigger={
                  <Button type="button" variant="outline" size="sm">
                    Revoke
                  </Button>
                }
                onConfirm={({ reason }) => handleRevoke(key.id, reason)}
              />
            ) : (
              <span className="text-sm text-text-muted">
                {key.revokedReason ?? "Revoked"}
              </span>
            ),
        }))}
      />
    </SectionPanel>
  );
}
