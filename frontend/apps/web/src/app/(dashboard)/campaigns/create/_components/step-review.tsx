"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { clientJson } from "@/lib/api/client";
import { apiEndpoints } from "@/lib/api/endpoints";
import { senderProfiles } from "@/app/(dashboard)/sender-profiles/_lib/sender-profiles-queries";
import { mockTemplates, getVersionsForTemplate } from "@/app/(dashboard)/templates/_lib/templates-queries";
import { mockSegments } from "@/app/(dashboard)/segments/_lib/segments-queries";
import { lists } from "@/app/(dashboard)/lists/_lib/lists-queries";
import { getMockPreflightChecks } from "@/app/(dashboard)/campaigns/_lib/campaigns-queries";
import type { CampaignDraft, CampaignRecord, PreflightSeverity } from "@/types/campaign";

const severityVariant: Record<PreflightSeverity, "success" | "warning" | "danger"> = {
  ok: "success",
  warning: "warning",
  critical: "danger",
};

const severityLabel: Record<PreflightSeverity, string> = {
  ok: "OK",
  warning: "Warning",
  critical: "Critical",
};

type StepReviewProps = {
  draft: CampaignDraft;
  onBack: () => void;
  onGoToStep: (step: number) => void;
  onLaunchSuccess: () => void;
};

export function StepReview({ draft, onBack, onGoToStep, onLaunchSuccess }: StepReviewProps) {
  const router = useRouter();
  const [launchOpen, setLaunchOpen] = useState(false);
  const [confirmName, setConfirmName] = useState("");
  const [isLaunching, setIsLaunching] = useState(false);

  const sender = senderProfiles.find((sp) => sp.id === draft.senderProfileId);
  const template = mockTemplates.find((t) => t.id === draft.templateId);
  const versions = draft.templateId ? getVersionsForTemplate(draft.templateId) : [];
  const templateVersion = versions.find((v) => v.version === draft.templateVersion);

  const audience =
    draft.audienceType === "segment"
      ? mockSegments.find((s) => s.id === draft.audienceId)
      : lists.find((l) => l.id === draft.audienceId);

  const audienceCount =
    draft.audienceType === "segment"
      ? (mockSegments.find((s) => s.id === draft.audienceId)?.lastComputedCount ?? 0)
      : (lists.find((l) => l.id === draft.audienceId)?.memberCount ?? 0);

  const preflightChecks = getMockPreflightChecks(audienceCount);
  const hasCritical = preflightChecks.some((c) => c.severity === "critical");
  const canLaunch = !hasCritical;

  async function handleLaunch() {
    if (confirmName !== draft.name || isLaunching) return;
    setIsLaunching(true);
    try {
      const campaign = await clientJson<CampaignRecord>(
        apiEndpoints.campaigns.create,
        {
          method: "POST",
          body: {
            name: draft.name,
            tag: draft.tag || null,
            senderProfileId: draft.senderProfileId,
            templateId: draft.templateId,
            templateVersion: draft.templateVersion,
            audienceType: draft.audienceType,
            audienceId: draft.audienceId,
            scheduleType: draft.scheduleType,
            scheduledAt: draft.scheduledAt || null,
            timezone: draft.timezone,
          },
        },
      );
      onLaunchSuccess();
      toast.success(`"${draft.name}" launched successfully.`);
      router.push(`/campaigns/${campaign.id}`);
    } catch {
      toast.error("Launch failed. Please retry or contact support.");
    } finally {
      setIsLaunching(false);
      setLaunchOpen(false);
    }
  }

  return (
    <div className="grid gap-6">
      {/* Summary */}
      <div className="surface-panel p-6 grid gap-5">
        <div className="flex items-center justify-between gap-3">
          <h2 className="section-title">Review</h2>
        </div>

        <dl className="summary-list">
          <div className="summary-row">
            <dt className="text-sm font-medium">Name</dt>
            <dd className="flex items-center gap-2">
              <span className="text-sm">{draft.name}</span>
              <button
                type="button"
                className="text-xs text-primary underline underline-offset-2"
                onClick={() => onGoToStep(0)}
              >
                Edit
              </button>
            </dd>
          </div>
          {draft.tag ? (
            <div className="summary-row">
              <dt className="text-sm font-medium">Tag</dt>
              <dd className="mono text-xs text-text-muted">{draft.tag}</dd>
            </div>
          ) : null}
          <div className="summary-row">
            <dt className="text-sm font-medium">Sender</dt>
            <dd className="flex items-center gap-2">
              <span className="text-sm">
                {sender ? `${sender.fromName} <${sender.fromEmail}>` : "—"}
              </span>
              <button
                type="button"
                className="text-xs text-primary underline underline-offset-2"
                onClick={() => onGoToStep(1)}
              >
                Edit
              </button>
            </dd>
          </div>
          <div className="summary-row">
            <dt className="text-sm font-medium">Template</dt>
            <dd className="flex items-center gap-2">
              <span className="text-sm">
                {template ? `${template.name} — v${draft.templateVersion}` : "—"}
              </span>
              <button
                type="button"
                className="text-xs text-primary underline underline-offset-2"
                onClick={() => onGoToStep(2)}
              >
                Edit
              </button>
            </dd>
          </div>
          {templateVersion ? (
            <div className="summary-row">
              <dt className="text-sm font-medium">Subject</dt>
              <dd className="text-sm text-text-muted italic">
                {templateVersion.subject}
              </dd>
            </div>
          ) : null}
          <div className="summary-row">
            <dt className="text-sm font-medium">Audience</dt>
            <dd className="flex items-center gap-2">
              <span className="text-sm">
                {audience ? audience.name : "—"}
                {audienceCount > 0 ? ` (${audienceCount.toLocaleString()})` : ""}
              </span>
              <button
                type="button"
                className="text-xs text-primary underline underline-offset-2"
                onClick={() => onGoToStep(3)}
              >
                Edit
              </button>
            </dd>
          </div>
          <div className="summary-row">
            <dt className="text-sm font-medium">Schedule</dt>
            <dd className="flex items-center gap-2">
              <span className="text-sm">
                {draft.scheduleType === "immediate"
                  ? "Send immediately"
                  : `${draft.scheduledAt} (${draft.timezone})`}
              </span>
              <button
                type="button"
                className="text-xs text-primary underline underline-offset-2"
                onClick={() => onGoToStep(4)}
              >
                Edit
              </button>
            </dd>
          </div>
        </dl>
      </div>

      {/* Pre-flight checks */}
      <div className="surface-panel p-6 grid gap-4">
        <h2 className="section-title">Pre-launch checks</h2>
        <ul role="list" className="grid gap-3">
          {preflightChecks.map((check) => (
            <li
              key={check.id}
              className="flex items-start justify-between gap-3"
            >
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium">{check.label}</p>
                <p className="text-xs text-text-muted mt-0.5">{check.detail}</p>
              </div>
              <Badge variant={severityVariant[check.severity]}>
                {severityLabel[check.severity]}
              </Badge>
            </li>
          ))}
        </ul>

        {hasCritical ? (
          <p role="alert" className="text-sm text-danger">
            One or more pre-launch checks are critical. Resolve them before launching.
          </p>
        ) : null}
      </div>

      <div className="flex justify-between gap-3">
        <Button type="button" variant="outline" onClick={onBack}>
          Back
        </Button>
        <Button
          type="button"
          disabled={!canLaunch}
          onClick={() => {
            setConfirmName("");
            setLaunchOpen(true);
          }}
        >
          Launch campaign
        </Button>
      </div>

      {/* Launch confirm dialog */}
      <Dialog
        open={launchOpen}
        onOpenChange={(open) => {
          if (!open) {
            setLaunchOpen(false);
            setConfirmName("");
          }
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Confirm launch</DialogTitle>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <p className="text-sm text-text-muted">
              This will immediately queue{" "}
              <strong>{audienceCount.toLocaleString()}</strong> sends (after
              suppression exclusions). This action cannot be undone without pausing.
            </p>
            <div>
              <label className="label" htmlFor="confirm-campaign-name">
                Type the campaign name to confirm
              </label>
              <Input
                id="confirm-campaign-name"
                value={confirmName}
                onChange={(e) => setConfirmName(e.target.value)}
                placeholder={draft.name}
                autoFocus
              />
              <p className="mt-1 text-xs text-text-muted">
                Type: <span className="font-medium">{draft.name}</span>
              </p>
            </div>
          </div>
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                setLaunchOpen(false);
                setConfirmName("");
              }}
            >
              Cancel
            </Button>
            <Button
              type="button"
              disabled={confirmName !== draft.name || isLaunching}
              onClick={() => void handleLaunch()}
            >
              {isLaunching ? "Launching…" : "Confirm launch"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
