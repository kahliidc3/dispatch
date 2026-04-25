"use client";

import { useState } from "react";
import { Plus } from "lucide-react";
import { toast } from "sonner";
import { ConfirmDialog } from "@/components/shared/confirm-dialog";
import { DataTable } from "@/components/shared/data-table";
import { SectionPanel } from "@/components/patterns/section-panel";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
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
import type { SettingsUserRecord, UserRole } from "@/types/api";

type UsersManagerProps = {
  initialUsers: SettingsUserRecord[];
};

type DraftUser = {
  name: string;
  email: string;
  role: UserRole;
  error: string | null;
};

function roleLabel(role: UserRole) {
  return role === "admin" ? "Admin" : "User";
}

function mfaBadgeVariant(mfaState: SettingsUserRecord["mfaState"]) {
  switch (mfaState) {
    case "enrolled":
      return "success";
    case "reset_required":
      return "warning";
    default:
      return "outline";
  }
}

export function UsersManager({ initialUsers }: UsersManagerProps) {
  const [users, setUsers] = useState(initialUsers);
  const [open, setOpen] = useState(false);
  const [draft, setDraft] = useState<DraftUser>({
    name: "",
    email: "",
    role: "user",
    error: null,
  });

  function resetDraft() {
    setDraft({
      name: "",
      email: "",
      role: "user",
      error: null,
    });
  }

  function handleCreate() {
    const name = draft.name.trim();
    const email = draft.email.trim().toLowerCase();

    if (name.length < 3 || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setDraft((current) => ({
        ...current,
        error: "Add a full name and a valid email address.",
      }));
      return;
    }

    setUsers((current) => [
      {
        id: crypto.randomUUID(),
        name,
        email,
        role: draft.role,
        status: "active",
        lastLoginAt: null,
        mfaState: "not_enrolled",
      },
      ...current,
    ]);
    setOpen(false);
    resetDraft();
    toast.success("User created.");
  }

  function handleToggleStatus(id: string, reason: string) {
    setUsers((current) =>
      current.map((user) =>
        user.id === id
          ? {
              ...user,
              status: user.status === "active" ? "disabled" : "active",
              mfaState:
                user.status === "active" ? "reset_required" : user.mfaState,
            }
          : user,
      ),
    );

    toast.success(reason.length > 0 ? "User status updated." : "User updated.");
  }

  function handleResetMfa(id: string) {
    setUsers((current) =>
      current.map((user) =>
        user.id === id
          ? {
              ...user,
              mfaState: "reset_required",
            }
          : user,
      ),
    );

    toast.success("MFA reset will be required at the next sign-in.");
  }

  return (
    <SectionPanel
      title="Operator access"
      description="Create internal users, disable dormant accounts, and force MFA reset without leaving the dashboard shell."
      actions={
        <Dialog
          open={open}
          onOpenChange={(nextOpen) => {
            setOpen(nextOpen);

            if (!nextOpen) {
              resetDraft();
            }
          }}
        >
          <DialogTrigger asChild>
            <Button type="button">
              <Plus className="h-4 w-4" />
              Create user
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create user</DialogTitle>
              <DialogDescription>
                Provision the operator record now. Backend delivery, invitation,
                and audit wiring will replace this local state in the API pass.
              </DialogDescription>
            </DialogHeader>
            <div className="grid gap-4">
              <div>
                <label className="label" htmlFor="user-name">
                  Full name
                </label>
                <Input
                  id="user-name"
                  value={draft.name}
                  placeholder="Campaign Operator"
                  onChange={(event) =>
                    setDraft((current) => ({
                      ...current,
                      name: event.target.value,
                      error: null,
                    }))
                  }
                />
              </div>
              <div>
                <label className="label" htmlFor="user-email">
                  Email
                </label>
                <Input
                  id="user-email"
                  type="email"
                  value={draft.email}
                  placeholder="operator@dispatch.internal"
                  onChange={(event) =>
                    setDraft((current) => ({
                      ...current,
                      email: event.target.value,
                      error: null,
                    }))
                  }
                />
              </div>
              <div>
                <label className="label" htmlFor="user-role">
                  Role
                </label>
                <select
                  id="user-role"
                  className="field"
                  value={draft.role}
                  onChange={(event) =>
                    setDraft((current) => ({
                      ...current,
                      role: event.target.value as UserRole,
                    }))
                  }
                >
                  <option value="user">User</option>
                  <option value="admin">Admin</option>
                </select>
              </div>
            </div>
            {draft.error ? (
              <p className="text-sm text-danger">{draft.error}</p>
            ) : null}
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setOpen(false)}>
                Cancel
              </Button>
              <Button type="button" onClick={handleCreate}>
                Create user
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      }
    >
      <DataTable
        caption="Dispatch operator accounts"
        columns={[
          { key: "name", label: "Name" },
          { key: "email", label: "Email" },
          { key: "role", label: "Role" },
          { key: "status", label: "Status" },
          { key: "lastLoginAt", label: "Last login" },
          { key: "mfaState", label: "MFA" },
          { key: "actions", label: "Actions" },
        ]}
        rows={users.map((user) => ({
          name: user.name,
          email: user.email,
          role: roleLabel(user.role),
          status: (
            <Badge variant={user.status === "active" ? "success" : "outline"}>
              {user.status}
            </Badge>
          ),
          lastLoginAt: user.lastLoginAt ? formatTimestamp(user.lastLoginAt) : "Never",
          mfaState: (
            <Badge variant={mfaBadgeVariant(user.mfaState)}>
              {user.mfaState.replace("_", " ")}
            </Badge>
          ),
          actions: (
            <div className="flex flex-wrap justify-end gap-2">
              <ConfirmDialog
                title={user.status === "active" ? "Disable user" : "Re-enable user"}
                description="Record why this access change is happening so the audit trail stays complete."
                confirmLabel={user.status === "active" ? "Disable user" : "Re-enable user"}
                requireReason
                reasonLabel="Reason"
                reasonPlaceholder="Dormant account, role change, or temporary suspension"
                trigger={
                  <Button type="button" variant="outline" size="sm">
                    {user.status === "active" ? "Disable" : "Re-enable"}
                  </Button>
                }
                onConfirm={({ reason }) => handleToggleStatus(user.id, reason)}
              />
              <Button
                type="button"
                variant="outline"
                size="sm"
                disabled={user.status !== "active"}
                onClick={() => handleResetMfa(user.id)}
              >
                Reset MFA
              </Button>
            </div>
          ),
        }))}
      />
    </SectionPanel>
  );
}
