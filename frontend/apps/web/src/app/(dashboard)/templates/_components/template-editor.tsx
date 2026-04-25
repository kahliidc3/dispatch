"use client";

import { useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import type { MergeTag, TemplateVersion } from "@/types/template";

const TAB_LABELS = ["Subject", "Plain text", "HTML"] as const;
type EditorTab = (typeof TAB_LABELS)[number];

type Draft = {
  subject: string;
  bodyText: string;
  bodyHtml: string;
};

function draftKey(templateId: string) {
  return `dispatch:template-draft:${templateId}`;
}

function loadDraft(templateId: string): Draft | null {
  try {
    const raw = localStorage.getItem(draftKey(templateId));
    return raw ? (JSON.parse(raw) as Draft) : null;
  } catch {
    return null;
  }
}

function saveDraft(templateId: string, draft: Draft) {
  try {
    localStorage.setItem(draftKey(templateId), JSON.stringify(draft));
  } catch {}
}

function clearDraft(templateId: string) {
  try {
    localStorage.removeItem(draftKey(templateId));
  } catch {}
}

type TemplateEditorProps = {
  templateId: string;
  initialVersion: TemplateVersion | null;
  mergeTags: MergeTag[];
  isSaving: boolean;
  onSave: (draft: Draft) => Promise<void>;
  onDraftChange: (draft: Draft) => void;
};

export function TemplateEditor({
  templateId,
  initialVersion,
  mergeTags,
  isSaving,
  onSave,
  onDraftChange,
}: TemplateEditorProps) {
  const [activeTab, setActiveTab] = useState<EditorTab>("Subject");
  const [subject, setSubject] = useState<string>(() => {
    const draft = loadDraft(templateId);
    return draft?.subject ?? initialVersion?.subject ?? "";
  });
  const [bodyText, setBodyText] = useState<string>(() => {
    const draft = loadDraft(templateId);
    return draft?.bodyText ?? initialVersion?.bodyText ?? "";
  });
  const [bodyHtml, setBodyHtml] = useState<string>(() => {
    const draft = loadDraft(templateId);
    return draft?.bodyHtml ?? initialVersion?.bodyHtml ?? "";
  });
  const [hasUnsaved, setHasUnsaved] = useState<boolean>(
    () => loadDraft(templateId) !== null,
  );
  const [showMergeTags, setShowMergeTags] = useState(false);
  const activeTextareaRef = useRef<HTMLTextAreaElement | null>(null);

  // Notify parent of draft changes for live preview
  useEffect(() => {
    onDraftChange({ subject, bodyText, bodyHtml });
  }, [subject, bodyText, bodyHtml, onDraftChange]);

  // Persist draft to localStorage on change
  useEffect(() => {
    if (!hasUnsaved) return;
    saveDraft(templateId, { subject, bodyText, bodyHtml });
  }, [templateId, subject, bodyText, bodyHtml, hasUnsaved]);

  // Guard: warn before navigating away with unsaved changes
  useEffect(() => {
    if (!hasUnsaved) return;
    function handleBeforeUnload(e: BeforeUnloadEvent) {
      e.preventDefault();
      e.returnValue = "";
    }
    window.addEventListener("beforeunload", handleBeforeUnload);
    return () => window.removeEventListener("beforeunload", handleBeforeUnload);
  }, [hasUnsaved]);

  function handleSubjectChange(value: string) {
    // Strip newlines from subject
    const clean = value.replace(/[\r\n]/g, "");
    setSubject(clean);
    setHasUnsaved(true);
  }

  function handleBodyTextChange(value: string) {
    setBodyText(value);
    setHasUnsaved(true);
  }

  function handleBodyHtmlChange(value: string) {
    setBodyHtml(value);
    setHasUnsaved(true);
  }

  function insertMergeTag(tag: string) {
    setShowMergeTags(false);
    if (activeTab === "Subject") {
      setSubject((prev) => prev + tag);
      setHasUnsaved(true);
      return;
    }
    const textarea = activeTextareaRef.current;
    if (!textarea) return;
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const value = textarea.value;
    const next = value.slice(0, start) + tag + value.slice(end);
    if (activeTab === "Plain text") {
      setBodyText(next);
    } else {
      setBodyHtml(next);
    }
    setHasUnsaved(true);
    setTimeout(() => {
      textarea.focus();
      const cursor = start + tag.length;
      textarea.setSelectionRange(cursor, cursor);
    }, 0);
  }

  async function handleSave() {
    await onSave({ subject, bodyText, bodyHtml });
    clearDraft(templateId);
    setHasUnsaved(false);
  }

  return (
    <section className="surface-panel p-6 grid gap-5">
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <h2 className="section-title">Editor</h2>
        <div className="flex items-center gap-2">
          {hasUnsaved ? (
            <span className="text-xs text-text-muted" role="status" aria-live="polite">
              Unsaved changes
            </span>
          ) : null}
          <div className="relative">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setShowMergeTags((v) => !v)}
              aria-expanded={showMergeTags}
              aria-haspopup="listbox"
            >
              Insert merge tag
            </Button>
            {showMergeTags ? (
              <ul
                role="listbox"
                aria-label="Available merge tags"
                className="absolute right-0 top-full z-10 mt-1 w-56 rounded-lg border border-border bg-surface shadow-md"
              >
                {mergeTags.map((mt) => (
                  <li key={mt.tag}>
                    <button
                      type="button"
                      role="option"
                      aria-selected={false}
                      className="w-full px-4 py-2 text-left text-sm hover:bg-surface-muted"
                      onClick={() => insertMergeTag(mt.tag)}
                    >
                      <span className="mono text-xs">{mt.tag}</span>
                      <span className="ml-2 text-text-muted">{mt.label}</span>
                    </button>
                  </li>
                ))}
              </ul>
            ) : null}
          </div>
        </div>
      </div>

      {/* Tab bar */}
      <div
        role="tablist"
        aria-label="Editor tabs"
        className="flex gap-1 border-b border-border"
      >
        {TAB_LABELS.map((tab) => (
          <button
            key={tab}
            type="button"
            role="tab"
            id={`tab-${tab}`}
            aria-selected={activeTab === tab}
            aria-controls={`tabpanel-${tab}`}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${
              activeTab === tab
                ? "border-primary text-foreground"
                : "border-transparent text-text-muted hover:text-foreground"
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Subject panel */}
      <div
        id="tabpanel-Subject"
        role="tabpanel"
        aria-labelledby="tab-Subject"
        hidden={activeTab !== "Subject"}
      >
        <label className="label" htmlFor="template-subject">
          Subject line
        </label>
        <Input
          id="template-subject"
          value={subject}
          onChange={(e) => handleSubjectChange(e.target.value)}
          placeholder="e.g. Quick note, {{first_name}}"
        />
        <p className="mt-1 text-xs text-text-muted">
          Newlines are stripped. Use merge tags for personalisation.
        </p>
      </div>

      {/* Plain text panel */}
      <div
        id="tabpanel-Plain text"
        role="tabpanel"
        aria-labelledby="tab-Plain text"
        hidden={activeTab !== "Plain text"}
      >
        <label className="label" htmlFor="template-body-text">
          Plain-text body
        </label>
        <textarea
          id="template-body-text"
          ref={activeTab === "Plain text" ? activeTextareaRef : undefined}
          className="field mono text-xs min-h-64 resize-y"
          value={bodyText}
          onChange={(e) => handleBodyTextChange(e.target.value)}
          placeholder="Plain-text version of your email…"
          spellCheck={false}
        />
      </div>

      {/* HTML panel */}
      <div
        id="tabpanel-HTML"
        role="tabpanel"
        aria-labelledby="tab-HTML"
        hidden={activeTab !== "HTML"}
      >
        <label className="label" htmlFor="template-body-html">
          HTML body
        </label>
        <textarea
          id="template-body-html"
          ref={activeTab === "HTML" ? activeTextareaRef : undefined}
          className="field mono text-xs min-h-64 resize-y"
          value={bodyHtml}
          onChange={(e) => handleBodyHtmlChange(e.target.value)}
          placeholder="<p>HTML version of your email…</p>"
          spellCheck={false}
        />
      </div>

      <div className="flex justify-end gap-3">
        <Button
          type="button"
          disabled={!hasUnsaved || isSaving}
          onClick={() => void handleSave()}
        >
          {isSaving ? "Saving…" : "Save as new version"}
        </Button>
      </div>
    </section>
  );
}
