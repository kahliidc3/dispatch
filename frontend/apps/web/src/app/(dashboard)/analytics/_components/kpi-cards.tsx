import type { OverviewKpi } from "../_lib/analytics-queries";

type KpiCardsProps = {
  kpis: OverviewKpi[];
};

export function KpiCards({ kpis }: KpiCardsProps) {
  return (
    <section aria-label="Key performance indicators">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {kpis.map((kpi) => (
          <div key={kpi.label} className="surface-panel p-5">
            <p className="text-xs font-medium uppercase tracking-wide text-text-muted">
              {kpi.label}
            </p>
            <p className="mt-2 text-2xl font-semibold tabular-nums tracking-tight">
              {kpi.value}
            </p>
            <p
              className={`mt-1 text-xs ${
                kpi.trendPositive ? "text-success" : "text-danger"
              }`}
            >
              {kpi.trendValue}
            </p>
          </div>
        ))}
      </div>
    </section>
  );
}
