"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
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
} from "@/components/ui/dialog";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { ConfirmDialog } from "@/components/shared/confirm-dialog";
import { clientJson } from "@/lib/api/client";
import { apiEndpoints } from "@/lib/api/endpoints";
import { formatTimestamp } from "@/lib/formatters";
import type { ContactLifecycle, ContactListItem } from "@/types/contact";
import type { List } from "@/types/list";

const LIFECYCLE_OPTIONS: Array<{ value: string; label: string }> = [
  { value: "all", label: "All statuses" },
  { value: "active", label: "Active" },
  { value: "bounced", label: "Bounced" },
  { value: "complained", label: "Complained" },
  { value: "unsubscribed", label: "Unsubscribed" },
  { value: "suppressed", label: "Suppressed" },
  { value: "deleted", label: "Deleted" },
];

const SOURCE_OPTIONS: Array<{ value: string; label: string }> = [
  { value: "all", label: "All sources" },
  { value: "csv_import", label: "CSV import" },
  { value: "api", label: "API" },
  { value: "manual", label: "Manual" },
  { value: "webhook", label: "Webhook" },
];

const lifecycleBadge: Record<
  ContactLifecycle,
  "success" | "danger" | "warning" | "muted"
> = {
  active: "success",
  suppressed: "danger",
  complained: "danger",
  unsubscribed: "warning",
  bounced: "muted",
  deleted: "muted",
};

type ContactsTableProps = {
  contacts: ContactListItem[];
  lists: List[];
};

export function ContactsTable({ contacts, lists }: ContactsTableProps) {
  const router = useRouter();
  const [search, setSearch] = useState("");
  const [lifecycle, setLifecycle] = useState("all");
  const [source, setSource] = useState("all");
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [addListOpen, setAddListOpen] = useState(false);
  const [removeListOpen, setRemoveListOpen] = useState(false);
  const [targetListId, setTargetListId] = useState("");

  const filtered = useMemo(() => {
    return contacts.filter((c) => {
      if (lifecycle !== "all" && c.lifecycle !== lifecycle) return false;
      if (source !== "all" && c.source !== source) return false;
      if (search && !c.email.toLowerCase().includes(search.toLowerCase())) {
        return false;
      }
      return true;
    });
  }, [contacts, lifecycle, source, search]);

  const allSelected =
    filtered.length > 0 && filtered.every((c) => selectedIds.has(c.id));

  function toggleAll() {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (allSelected) {
        filtered.forEach((c) => next.delete(c.id));
      } else {
        filtered.forEach((c) => next.add(c.id));
      }
      return next;
    });
  }

  function toggleRow(id: string) {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  async function handleBulkUnsubscribe() {
    try {
      await clientJson(apiEndpoints.contacts.bulkUnsubscribe, {
        method: "POST",
        body: { contactIds: Array.from(selectedIds) },
      });
      toast.success(`${selectedIds.size} contact(s) unsubscribed.`);
      setSelectedIds(new Set());
      router.refresh();
    } catch {
      toast.error("Bulk unsubscribe failed. Please try again.");
    }
  }

  async function handleAddToList() {
    if (!targetListId) return;
    try {
      for (const contactId of selectedIds) {
        await clientJson(apiEndpoints.lists.addMember(targetListId), {
          method: "POST",
          body: { contactId },
        });
      }
      toast.success(`Added ${selectedIds.size} contact(s) to list.`);
      setAddListOpen(false);
      setTargetListId("");
      setSelectedIds(new Set());
      router.refresh();
    } catch {
      toast.error("Could not add contacts to list.");
    }
  }

  async function handleRemoveFromList() {
    if (!targetListId) return;
    try {
      for (const contactId of selectedIds) {
        await clientJson(
          apiEndpoints.lists.removeMember(targetListId, contactId),
          { method: "DELETE" },
        );
      }
      toast.success(`Removed ${selectedIds.size} contact(s) from list.`);
      setRemoveListOpen(false);
      setTargetListId("");
      setSelectedIds(new Set());
      router.refresh();
    } catch {
      toast.error("Could not remove contacts from list.");
    }
  }

  const selectionCount = selectedIds.size;

  return (
    <div className="grid gap-3">
      <div className="flex flex-wrap items-center gap-3">
        <input
          type="search"
          className="field h-9 w-64"
          placeholder="Search by email…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          aria-label="Search contacts by email"
        />
        <select
          className="field h-9"
          aria-label="Filter by lifecycle status"
          value={lifecycle}
          onChange={(e) => setLifecycle(e.target.value)}
        >
          {LIFECYCLE_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>
        <select
          className="field h-9"
          aria-label="Filter by source"
          value={source}
          onChange={(e) => setSource(e.target.value)}
        >
          {SOURCE_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>
      </div>

      {selectionCount > 0 && (
        <div className="surface-panel-muted flex flex-wrap items-center gap-3 rounded-lg px-4 py-3">
          <span className="text-sm font-medium">{selectionCount} selected</span>
          <ConfirmDialog
            title="Bulk unsubscribe"
            description={`This will unsubscribe ${selectionCount} contact(s) from all email. They will no longer receive messages.`}
            trigger={
              <Button type="button" variant="outline" size="sm">
                Unsubscribe
              </Button>
            }
            confirmLabel="Unsubscribe all"
            onConfirm={() => handleBulkUnsubscribe()}
          />
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => {
              setTargetListId(lists[0]?.id ?? "");
              setAddListOpen(true);
            }}
          >
            Add to list
          </Button>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => {
              setTargetListId(lists[0]?.id ?? "");
              setRemoveListOpen(true);
            }}
          >
            Remove from list
          </Button>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => setSelectedIds(new Set())}
          >
            Clear
          </Button>
        </div>
      )}

      <div className="surface-panel overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-10">
                <input
                  type="checkbox"
                  aria-label="Select all visible contacts"
                  checked={allSelected}
                  onChange={toggleAll}
                  className="h-4 w-4"
                />
              </TableHead>
              <TableHead>Contact</TableHead>
              <TableHead>Lifecycle</TableHead>
              <TableHead>Source</TableHead>
              <TableHead className="text-right">Updated</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filtered.length > 0 ? (
              filtered.map((contact) => (
                <TableRow key={contact.id}>
                  <TableCell>
                    <input
                      type="checkbox"
                      aria-label={`Select ${contact.email}`}
                      checked={selectedIds.has(contact.id)}
                      onChange={() => toggleRow(contact.id)}
                      className="h-4 w-4"
                    />
                  </TableCell>
                  <TableCell>
                    <Link
                      href={`/contacts/${contact.id}`}
                      className="font-medium hover:underline"
                    >
                      {contact.email}
                    </Link>
                    {(contact.firstName ?? contact.lastName) ? (
                      <p className="text-xs text-text-muted">
                        {[contact.firstName, contact.lastName]
                          .filter(Boolean)
                          .join(" ")}
                      </p>
                    ) : null}
                  </TableCell>
                  <TableCell>
                    <Badge variant={lifecycleBadge[contact.lifecycle]}>
                      {contact.lifecycle}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-sm text-text-muted">
                    {contact.source.replace("_", " ")}
                  </TableCell>
                  <TableCell className="text-right text-sm text-text-muted">
                    {formatTimestamp(contact.updatedAt)}
                  </TableCell>
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell
                  colSpan={5}
                  className="px-4 py-10 text-sm text-text-muted"
                >
                  No contacts match the current filters.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>

      <Dialog
        open={addListOpen}
        onOpenChange={(o) => {
          setAddListOpen(o);
          if (!o) setTargetListId("");
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add to list</DialogTitle>
            <DialogDescription>
              Choose a list to add the {selectionCount} selected contact(s) to.
            </DialogDescription>
          </DialogHeader>
          {lists.length > 0 ? (
            <div>
              <label className="label" htmlFor="bulk-add-list-select">
                List
              </label>
              <select
                id="bulk-add-list-select"
                className="field h-9 w-full"
                value={targetListId}
                onChange={(e) => setTargetListId(e.target.value)}
              >
                {lists.map((l) => (
                  <option key={l.id} value={l.id}>
                    {l.name}
                  </option>
                ))}
              </select>
            </div>
          ) : (
            <p className="text-sm text-text-muted">
              No lists available. Create a list first.
            </p>
          )}
          <DialogFooter>
            <DialogClose asChild>
              <Button type="button" variant="outline">
                Cancel
              </Button>
            </DialogClose>
            <Button
              type="button"
              disabled={!targetListId}
              onClick={() => void handleAddToList()}
            >
              Add to list
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog
        open={removeListOpen}
        onOpenChange={(o) => {
          setRemoveListOpen(o);
          if (!o) setTargetListId("");
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Remove from list</DialogTitle>
            <DialogDescription>
              Choose a list to remove the {selectionCount} selected contact(s)
              from.
            </DialogDescription>
          </DialogHeader>
          {lists.length > 0 ? (
            <div>
              <label className="label" htmlFor="bulk-remove-list-select">
                List
              </label>
              <select
                id="bulk-remove-list-select"
                className="field h-9 w-full"
                value={targetListId}
                onChange={(e) => setTargetListId(e.target.value)}
              >
                {lists.map((l) => (
                  <option key={l.id} value={l.id}>
                    {l.name}
                  </option>
                ))}
              </select>
            </div>
          ) : (
            <p className="text-sm text-text-muted">No lists available.</p>
          )}
          <DialogFooter>
            <DialogClose asChild>
              <Button type="button" variant="outline">
                Cancel
              </Button>
            </DialogClose>
            <Button
              type="button"
              disabled={!targetListId}
              onClick={() => void handleRemoveFromList()}
            >
              Remove from list
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
