import { chartTheme } from "@/lib/chart-theme";

type LineChartPoint = {
  label: string;
  value: number;
};

type LineChartProps = {
  points?: LineChartPoint[];
};

const defaultPoints: LineChartPoint[] = [
  { label: "Mon", value: 18 },
  { label: "Tue", value: 26 },
  { label: "Wed", value: 21 },
  { label: "Thu", value: 34 },
  { label: "Fri", value: 29 },
];

export function LineChart({ points = defaultPoints }: LineChartProps) {
  const max = Math.max(...points.map((point) => point.value), 1);

  const coordinates = points
    .map((point, index) => {
      const x = index * (100 / Math.max(points.length - 1, 1));
      const y = 100 - (point.value / max) * 100;
      return `${x},${y}`;
    })
    .join(" ");

  return (
    <div className="surface-panel p-5">
      <div className="flex items-baseline justify-between gap-3">
        <h3 className="section-title">Trend placeholder</h3>
        <span className="mono text-xs text-text-muted">static sample</span>
      </div>
      <svg
        viewBox="0 0 100 100"
        className="mt-4 h-40 w-full overflow-visible"
        preserveAspectRatio="none"
        aria-hidden="true"
      >
        {[20, 40, 60, 80].map((offset) => (
          <line
            key={offset}
            x1="0"
            x2="100"
            y1={offset}
            y2={offset}
            stroke={chartTheme.grid}
            strokeDasharray="2 3"
            strokeWidth="0.5"
          />
        ))}
        <polyline
          fill="none"
          points={coordinates}
          stroke={chartTheme.line}
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth="2.5"
        />
      </svg>
      <div className="mt-3 flex justify-between text-xs text-text-muted">
        {points.map((point) => (
          <span key={point.label}>{point.label}</span>
        ))}
      </div>
    </div>
  );
}
