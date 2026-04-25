"use client";

import { useCallback, useState } from "react";
import { toast } from "sonner";
import { clientJson } from "@/lib/api/client";
import { apiEndpoints } from "@/lib/api/endpoints";
import { TemplateEditor } from "./template-editor";
import { PreviewPane } from "./preview-pane";
import { VersionHistory } from "./version-history";
import type { Template, TemplateVersion, MergeTag } from "@/types/template";

type Draft = {
  subject: string;
  bodyText: string;
  bodyHtml: string;
};

type TemplateWorkspaceProps = {
  template: Template;
  versions: TemplateVersion[];
  mergeTags: MergeTag[];
};

export function TemplateWorkspace({
  template,
  versions: initialVersions,
  mergeTags,
}: TemplateWorkspaceProps) {
  const [versions, setVersions] = useState<TemplateVersion[]>(initialVersions);
  const [isSaving, setIsSaving] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const [selectedVersion, setSelectedVersion] = useState<TemplateVersion | null>(
    () => {
      const active = initialVersions.find(
        (v) => v.version === template.activeVersion,
      );
      return active ?? initialVersions.at(-1) ?? null;
    },
  );
  const [previewDraft, setPreviewDraft] = useState<Draft>({
    subject: selectedVersion?.subject ?? "",
    bodyText: selectedVersion?.bodyText ?? "",
    bodyHtml: selectedVersion?.bodyHtml ?? "",
  });

  const handleDraftChange = useCallback((draft: Draft) => {
    setPreviewDraft(draft);
  }, []);

  async function handleSave(draft: Draft) {
    setIsSaving(true);
    try {
      const newVersion = await clientJson<TemplateVersion>(
        apiEndpoints.templates.versions(template.id),
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(draft),
        },
      );
      setVersions((prev) => [...prev, newVersion]);
      setSelectedVersion(newVersion);
      toast.success(`Version ${newVersion.version} saved.`);
    } catch {
      toast.error("Failed to save version. Please try again.");
    } finally {
      setIsSaving(false);
    }
  }

  async function handleRestore(version: TemplateVersion) {
    setIsSaving(true);
    try {
      const newVersion = await clientJson<TemplateVersion>(
        apiEndpoints.templates.versions(template.id),
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            subject: version.subject,
            bodyText: version.bodyText,
            bodyHtml: version.bodyHtml,
          }),
        },
      );
      setVersions((prev) => [...prev, newVersion]);
      setSelectedVersion(newVersion);
      toast.success(
        `v${version.version} restored as v${newVersion.version}.`,
      );
    } catch {
      toast.error("Failed to restore version. Please try again.");
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <div className="grid gap-5">
      <div className="flex justify-end">
        <button
          type="button"
          className="text-sm text-primary underline underline-offset-2 hover:no-underline"
          onClick={() => setShowHistory((v) => !v)}
          aria-expanded={showHistory}
        >
          {showHistory ? "Hide version history" : "Show version history"}
        </button>
      </div>

      {showHistory ? (
        <VersionHistory
          versions={versions}
          activeVersion={template.activeVersion}
          onRestore={handleRestore}
          onSelect={setSelectedVersion}
          selectedVersion={selectedVersion}
        />
      ) : null}

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1.2fr)_minmax(0,0.8fr)]">
        <TemplateEditor
          templateId={template.id}
          initialVersion={selectedVersion}
          mergeTags={mergeTags}
          isSaving={isSaving}
          onSave={handleSave}
          onDraftChange={handleDraftChange}
        />
        <PreviewPane
          subject={previewDraft.subject}
          bodyHtml={previewDraft.bodyHtml}
          bodyText={previewDraft.bodyText}
        />
      </div>
    </div>
  );
}
