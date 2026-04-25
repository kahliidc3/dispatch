import Link from "next/link";
import type { TopCampaignRow } from "../_lib/analytics-queries";

function Sparkline({ values }: { values: number[] }) {
  const max = Math.max(...values, 1);
  const w = 64;
  const h = 24;
  const step = w / (values.length - 1);
  const points = values
    .map((v, i) => `${i * step},${h - (v / max) * h}`)
    .join(" ");
  return (
    <svg
      width={w}
      height={h}
      aria-hidden="true"
      className="shrink-0"
      viewBox={`0 0 ${w} ${h}`}
    >
      <polyline
        points={points}
        fill="none"
        stroke="var(--chart-1)"
        strokeWidth="1.5"
        strokeLinejoin="round"
        strokeLinecap="round"
      />
    </svg>
  );
}

type TopCampaignsProps = {
  rows: TopCampaignRow[];
};

export function TopCampaigns({ rows }: TopCampaignsProps) {
  return (
    <section className="surface-panel p-5">
      <h2 className="section-title mb-4">Top campaigns — last 7 days</h2>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border text-left">
              <th className="pb-2 pr-4 font-medium text-text-muted">Campaign</th>
              <th className="pb-2 pr-4 font-medium text-text-muted text-right">
                Sends
              </th>
              <th className="pb-2 pr-4 font-medium text-text-muted text-right">
                Open rate
              </th>
              <th className="pb-2 font-medium text-text-muted">Trend</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.id} className="border-b border-border/50">
                <td className="py-2.5 pr-4">
                  <Link
                    href={`/campaigns/${row.id}`}
                    className="font-medium hover:underline"
                  >
                    {row.name}
                  </Link>
                </td>
                <td className="py-2.5 pr-4 mono text-right tabular-nums">
                  {row.sends.toLocaleString()}
                </td>
                <td className="py-2.5 pr-4 mono text-right tabular-nums">
                  {row.openRate > 0 ? `${row.openRate.toFixed(1)}%` : "—"}
                </td>
                <td className="py-2.5">
                  <Sparkline values={row.sparkline} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
