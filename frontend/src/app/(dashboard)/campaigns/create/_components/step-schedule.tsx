"use client";

import { Button } from "@/components/ui/button";
import type { CampaignDraft } from "@/types/campaign";

const TIMEZONES = [
  "UTC",
  "America/New_York",
  "America/Chicago",
  "America/Denver",
  "America/Los_Angeles",
  "Europe/London",
  "Europe/Paris",
  "Europe/Berlin",
  "Asia/Tokyo",
  "Asia/Singapore",
  "Australia/Sydney",
];

type StepScheduleProps = {
  draft: CampaignDraft;
  onChange: (patch: Partial<CampaignDraft>) => void;
  onBack: () => void;
  onNext: () => void;
};

export function StepSchedule({ draft, onChange, onBack, onNext }: StepScheduleProps) {
  const canContinue =
    draft.scheduleType === "immediate" || draft.scheduledAt !== "";

  return (
    <div className="grid gap-6">
      <div className="surface-panel p-6 grid gap-5">
        <fieldset>
          <legend className="label mb-3">When to send</legend>
          <div className="grid gap-3">
            <label
              className={`flex cursor-pointer items-start gap-4 rounded-lg border p-4 transition-colors ${
                draft.scheduleType === "immediate"
                  ? "border-primary bg-primary/5"
                  : "border-border hover:border-primary/40"
              }`}
            >
              <input
                type="radio"
                name="schedule-type"
                value="immediate"
                checked={draft.scheduleType === "immediate"}
                onChange={() =>
                  onChange({ scheduleType: "immediate", scheduledAt: "" })
                }
                className="mt-0.5"
              />
              <div>
                <p className="font-medium text-sm">Send immediately</p>
                <p className="text-xs text-text-muted mt-0.5">
                  Campaign enters the send queue as soon as you launch.
                </p>
              </div>
            </label>

            <label
              className={`flex cursor-pointer items-start gap-4 rounded-lg border p-4 transition-colors ${
                draft.scheduleType === "scheduled"
                  ? "border-primary bg-primary/5"
                  : "border-border hover:border-primary/40"
              }`}
            >
              <input
                type="radio"
                name="schedule-type"
                value="scheduled"
                checked={draft.scheduleType === "scheduled"}
                onChange={() => onChange({ scheduleType: "scheduled" })}
                className="mt-0.5"
              />
              <div className="flex-1">
                <p className="font-medium text-sm">Schedule for later</p>
                <p className="text-xs text-text-muted mt-0.5">
                  Set a specific date and time.
                </p>
              </div>
            </label>
          </div>
        </fieldset>

        {draft.scheduleType === "scheduled" ? (
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label className="label" htmlFor="scheduled-at">
                Date and time
              </label>
              <input
                id="scheduled-at"
                type="datetime-local"
                className="field h-9 w-full"
                value={draft.scheduledAt}
                onChange={(e) => onChange({ scheduledAt: e.target.value })}
              />
            </div>
            <div>
              <label className="label" htmlFor="timezone">
                Timezone
              </label>
              <select
                id="timezone"
                className="field h-9 w-full"
                value={draft.timezone}
                onChange={(e) => onChange({ timezone: e.target.value })}
              >
                {TIMEZONES.map((tz) => (
                  <option key={tz} value={tz}>
                    {tz}
                  </option>
                ))}
              </select>
            </div>
          </div>
        ) : null}
      </div>

      <div className="flex justify-between gap-3">
        <Button type="button" variant="outline" onClick={onBack}>
          Back
        </Button>
        <Button type="button" disabled={!canContinue} onClick={onNext}>
          Continue to review
        </Button>
      </div>
    </div>
  );
}
