"use client";

import { useMemo, useState } from "react";
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

type ConfirmDialogProps = {
  title: string;
  description: string;
  triggerLabel?: string;
  trigger?: React.ReactNode;
  confirmLabel?: string;
  cancelLabel?: string;
  confirmVariant?: "default" | "outline";
  requireReason?: boolean;
  reasonLabel?: string;
  reasonPlaceholder?: string;
  onConfirm?: (context: { reason: string }) => Promise<void> | void;
};

export function ConfirmDialog({
  title,
  description,
  triggerLabel = "Open",
  trigger,
  confirmLabel = "Confirm",
  cancelLabel = "Cancel",
  confirmVariant = "default",
  requireReason = false,
  reasonLabel = "Reason",
  reasonPlaceholder = "Add context for the audit trail",
  onConfirm,
}: ConfirmDialogProps) {
  const [open, setOpen] = useState(false);
  const [reason, setReason] = useState("");
  const [isPending, setIsPending] = useState(false);
  const isReasonValid = useMemo(
    () => (requireReason ? reason.trim().length > 0 : true),
    [reason, requireReason],
  );

  async function handleConfirm() {
    if (!isReasonValid) {
      return;
    }

    setIsPending(true);

    try {
      await onConfirm?.({
        reason: reason.trim(),
      });
      setOpen(false);
      setReason("");
    } finally {
      setIsPending(false);
    }
  }

  return (
    <Dialog
      open={open}
      onOpenChange={(nextOpen) => {
        setOpen(nextOpen);
        if (!nextOpen) {
          setReason("");
        }
      }}
    >
      <DialogTrigger asChild>
        {trigger ?? (
          <Button type="button" variant="outline">
            {triggerLabel}
          </Button>
        )}
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
          <DialogDescription>{description}</DialogDescription>
        </DialogHeader>
        {requireReason ? (
          <div>
            <label className="label" htmlFor="confirm-dialog-reason">
              {reasonLabel}
            </label>
            <Input
              id="confirm-dialog-reason"
              value={reason}
              onChange={(event) => setReason(event.target.value)}
              placeholder={reasonPlaceholder}
            />
            {!isReasonValid ? (
              <p className="mt-2 text-sm text-danger">
                A short reason is required before this action can continue.
              </p>
            ) : null}
          </div>
        ) : null}
        <DialogFooter>
          <DialogClose asChild>
            <Button type="button" variant="outline">
              {cancelLabel}
            </Button>
          </DialogClose>
          <Button
            type="button"
            variant={confirmVariant}
            disabled={isPending || !isReasonValid}
            onClick={() => void handleConfirm()}
          >
            {isPending ? "Working..." : confirmLabel}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
