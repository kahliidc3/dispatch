"use client";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import type { CampaignDraft } from "@/types/campaign";

type StepDetailsProps = {
  draft: CampaignDraft;
  onChange: (patch: Partial<CampaignDraft>) => void;
  onNext: () => void;
};

export function StepDetails({ draft, onChange, onNext }: StepDetailsProps) {
  const canContinue = draft.name.trim().length > 0;

  return (
    <div className="grid gap-6">
      <div className="surface-panel p-6 grid gap-5">
        <div>
          <label className="label" htmlFor="campaign-name">
            Campaign name <span className="text-danger">*</span>
          </label>
          <Input
            id="campaign-name"
            value={draft.name}
            onChange={(e) => onChange({ name: e.target.value })}
            placeholder="e.g. April warmup cohort"
            autoFocus
          />
        </div>
        <div>
          <label className="label" htmlFor="campaign-tag">
            Internal tag{" "}
            <span className="font-normal text-text-muted">(optional)</span>
          </label>
          <Input
            id="campaign-tag"
            value={draft.tag}
            onChange={(e) => onChange({ tag: e.target.value })}
            placeholder="e.g. q2-warmup, ops-seed"
          />
          <p className="mt-1 text-xs text-text-muted">
            Tags are internal only — not visible to recipients.
          </p>
        </div>
      </div>

      <div className="flex justify-end">
        <Button
          type="button"
          disabled={!canContinue}
          onClick={onNext}
        >
          Continue
        </Button>
      </div>
    </div>
  );
}
