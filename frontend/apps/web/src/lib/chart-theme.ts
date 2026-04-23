export const chartTheme = {
  line: "var(--chart-1)",
  comparison: "var(--chart-2)",
  support: "var(--chart-3)",
  neutral: "var(--chart-4)",
  grid: "var(--border-subtle)",
  label: "var(--text-muted)",
  heatmap(value: number) {
    if (value >= 4) return "var(--success-bg)";
    if (value >= 3) return "color-mix(in srgb, var(--chart-1) 22%, white)";
    if (value >= 2) return "var(--warning-bg)";
    if (value >= 1) return "color-mix(in srgb, var(--chart-3) 10%, white)";
    return "rgba(124, 91, 67, 0.06)";
  },
};
