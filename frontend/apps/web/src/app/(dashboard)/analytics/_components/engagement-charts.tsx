import { Heatmap } from "@/components/charts/heatmap";
import { LineChart } from "@/components/charts/line-chart";

export function EngagementCharts() {
  return (
    <section className="grid gap-4 xl:grid-cols-2">
      <LineChart />
      <Heatmap />
    </section>
  );
}
