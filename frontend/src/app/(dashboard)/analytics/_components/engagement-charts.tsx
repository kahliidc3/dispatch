"use client";

import { useMemo } from "react";
import ReactEChartsCore from "echarts-for-react/lib/core";
import { CanvasRenderer } from "echarts/renderers";
import { LineChart as EChartsLineChart } from "echarts/charts";
import { HeatmapChart as EChartsHeatmapChart } from "echarts/charts";
import {
  GridComponent,
  LegendComponent,
  TooltipComponent,
  VisualMapComponent,
} from "echarts/components";
import * as echarts from "echarts/core";
import { chartTheme } from "@/lib/chart-theme";
import type { TimeSeriesPoint } from "../_lib/analytics-queries";
import { HEATMAP_HOUR_LABELS, HEATMAP_DAY_LABELS } from "../_lib/analytics-queries";

echarts.use([
  CanvasRenderer,
  EChartsLineChart,
  EChartsHeatmapChart,
  GridComponent,
  LegendComponent,
  TooltipComponent,
  VisualMapComponent,
]);

type TimeSeriesChartProps = {
  points: TimeSeriesPoint[];
};

function TimeSeriesChart({ points }: TimeSeriesChartProps) {
  const option = useMemo(
    () => ({
      animationDuration: 200,
      color: [chartTheme.line, chartTheme.comparison, chartTheme.support],
      grid: { top: 32, right: 16, bottom: 24, left: 16, containLabel: true },
      legend: {
        bottom: 0,
        icon: "circle",
        itemHeight: 8,
        itemWidth: 8,
        textStyle: { color: chartTheme.label, fontFamily: "IBM Plex Sans" },
      },
      tooltip: {
        trigger: "axis",
        backgroundColor: chartTheme.tooltipBackground,
        borderColor: chartTheme.grid,
        textStyle: { color: chartTheme.tooltipText, fontFamily: "IBM Plex Sans" },
      },
      xAxis: {
        type: "category",
        data: points.map((p) => p.label),
        axisLine: { lineStyle: { color: chartTheme.grid } },
        axisTick: { show: false },
        axisLabel: { color: chartTheme.label, fontFamily: "IBM Plex Sans", interval: 2 },
      },
      yAxis: {
        type: "value",
        splitNumber: 4,
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: { color: chartTheme.label, fontFamily: "IBM Plex Mono" },
        splitLine: { lineStyle: { color: chartTheme.grid } },
      },
      series: [
        {
          name: "Sent",
          type: "line",
          data: points.map((p) => p.sent),
          smooth: false,
          symbolSize: 4,
          lineStyle: { width: 2 },
        },
        {
          name: "Delivered",
          type: "line",
          data: points.map((p) => p.delivered),
          smooth: false,
          symbolSize: 4,
          lineStyle: { width: 2 },
        },
        {
          name: "Bounced",
          type: "line",
          data: points.map((p) => p.bounced),
          smooth: false,
          symbolSize: 4,
          lineStyle: { width: 2 },
        },
      ],
    }),
    [points],
  );

  return (
    <div className="surface-panel p-5">
      <h3 className="section-title">Sends over time</h3>
      <ReactEChartsCore
        echarts={echarts}
        option={option}
        notMerge
        lazyUpdate
        opts={{ renderer: "canvas" }}
        style={{ height: 280, width: "100%", marginTop: 16 }}
      />
    </div>
  );
}

type OpenRateHeatmapProps = {
  cells: number[][];
};

function OpenRateHeatmap({ cells }: OpenRateHeatmapProps) {
  const flatData = cells.flatMap((row, rowIdx) =>
    row.map((value, colIdx) => [colIdx, rowIdx, value]),
  );

  const option = useMemo(
    () => ({
      animationDuration: 200,
      grid: { top: 16, right: 40, bottom: 32, left: 48 },
      tooltip: {
        position: "top",
        backgroundColor: chartTheme.tooltipBackground,
        borderColor: chartTheme.grid,
        textStyle: { color: chartTheme.tooltipText, fontFamily: "IBM Plex Sans" },
        formatter: (params: { data: number[] }) =>
          `${params.data[2]}% open rate`,
      },
      xAxis: {
        type: "category",
        data: HEATMAP_HOUR_LABELS,
        splitArea: { show: false },
        axisLine: { lineStyle: { color: chartTheme.grid } },
        axisLabel: {
          color: chartTheme.label,
          fontFamily: "IBM Plex Mono",
          fontSize: 10,
          interval: 1,
        },
      },
      yAxis: {
        type: "category",
        data: HEATMAP_DAY_LABELS,
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: { color: chartTheme.label, fontFamily: "IBM Plex Sans" },
      },
      visualMap: {
        show: false,
        min: 0,
        max: 50,
        inRange: { color: chartTheme.heatmapScale },
      },
      series: [
        {
          type: "heatmap",
          data: flatData,
          label: { show: false },
          emphasis: {
            itemStyle: { borderColor: chartTheme.grid, borderWidth: 1 },
          },
        },
      ],
    }),
    [flatData],
  );

  return (
    <div className="surface-panel p-5">
      <h3 className="section-title">Open rate by hour × day</h3>
      <p className="text-xs text-text-muted mt-0.5">% open rate per 2-hour window</p>
      <ReactEChartsCore
        echarts={echarts}
        option={option}
        notMerge
        lazyUpdate
        opts={{ renderer: "canvas" }}
        style={{ height: 280, width: "100%", marginTop: 16 }}
      />
    </div>
  );
}

type EngagementChartsProps = {
  timeSeries: TimeSeriesPoint[];
  heatmapCells: number[][];
};

export function EngagementCharts({ timeSeries, heatmapCells }: EngagementChartsProps) {
  return (
    <section className="grid gap-4 xl:grid-cols-2" aria-label="Engagement charts">
      <TimeSeriesChart points={timeSeries} />
      <OpenRateHeatmap cells={heatmapCells} />
    </section>
  );
}
