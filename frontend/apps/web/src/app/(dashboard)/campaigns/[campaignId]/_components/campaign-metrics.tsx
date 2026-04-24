"use client";

import { LineChart } from "@/components/charts/line-chart";
import type { CampaignKpis, VelocityPoint } from "@/types/campaign";

type FunnelStep = { label: string; value: number; color: string };

function CampaignFunnel({ kpis }: { kpis: CampaignKpis }) {
  const steps: FunnelStep[] = [
    { label: "Sent", value: kpis.sent, color: "bg-[var(--chart-1)]" },
    { label: "Delivered", value: kpis.delivered, color: "bg-[var(--chart-1)]" },
    { label: "Opened", value: kpis.opened, color: "bg-[var(--chart-3)]" },
    { label: "Clicked", value: kpis.clicked, color: "bg-[var(--chart-3)]" },
  ];
  const max = Math.max(...steps.map((s) => s.value), 1);

  return (
    <div className="surface-panel p-5">
      <h3 className="section-title mb-4">Send funnel</h3>
      <div className="grid gap-3">
        {steps.map((step, i) => {
          const pct = Math.round((step.value / max) * 100);
          const convPct =
            i > 0 && steps[i - 1]!.value > 0
              ? ((step.value / steps[i - 1]!.value) * 100).toFixed(1)
              : null;
          return (
            <div key={step.label}>
              <div className="flex items-baseline justify-between gap-2 mb-1">
                <span className="text-sm font-medium">{step.label}</span>
                <span className="mono text-sm tabular-nums">
                  {step.value.toLocaleString()}
                  {convPct !== null && (
                    <span className="text-xs text-text-muted ml-1.5">
                      {convPct}%
                    </span>
                  )}
                </span>
              </div>
              <div className="h-2 w-full rounded-full bg-surface-muted overflow-hidden">
                <div
                  className={`h-full rounded-full ${step.color} transition-all`}
                  style={{ width: `${pct}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

type CampaignMetricsProps = {
  kpis: CampaignKpis;
  velocityPoints: VelocityPoint[];
};

export function CampaignMetrics({ kpis, velocityPoints }: CampaignMetricsProps) {
  return (
    <section className="grid gap-4 xl:grid-cols-2">
      <CampaignFunnel kpis={kpis} />
      <LineChart
        points={velocityPoints.map((p) => ({ label: p.label, value: p.value }))}
        title="Send velocity"
        detailLabel="sends / min"
      />
    </section>
  );
}
