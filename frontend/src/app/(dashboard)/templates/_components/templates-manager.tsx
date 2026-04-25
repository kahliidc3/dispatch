"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { clientJson } from "@/lib/api/client";
import { apiEndpoints } from "@/lib/api/endpoints";
import type { Template } from "@/types/template";


export function TemplatesManager() {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [isSaving, setIsSaving] = useState(false);

  async function handleCreate() {
    if (!name.trim()) return;
    setIsSaving(true);
    try {
      const template = await clientJson<Template>(apiEndpoints.templates.create, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: name.trim(), description: description.trim() || null }),
      });
      toast.success("Template created.");
      setOpen(false);
      setName("");
      setDescription("");
      router.push(`/templates/${template.id}`);
      router.refresh();
    } catch {
      toast.error("Failed to create template.");
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <>
      <Button type="button" onClick={() => setOpen(true)}>
        New template
      </Button>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create template</DialogTitle>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div>
              <label className="label" htmlFor="new-template-name">
                Name
              </label>
              <Input
                id="new-template-name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Warmup plain text"
                autoFocus
              />
            </div>
            <div>
              <label className="label" htmlFor="new-template-description">
                Description{" "}
                <span className="text-text-muted font-normal">(optional)</span>
              </label>
              <Input
                id="new-template-description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Short description of this template's purpose"
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => setOpen(false)}
            >
              Cancel
            </Button>
            <Button
              type="button"
              disabled={!name.trim() || isSaving}
              onClick={() => void handleCreate()}
            >
              {isSaving ? "Creating…" : "Create"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
