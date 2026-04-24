"use client";

import { useMemo } from "react";
import ReactEChartsCore from "echarts-for-react/lib/core";
import { CanvasRenderer } from "echarts/renderers";
import { LineChart as EChartsLineChart } from "echarts/charts";
import {
  GridComponent,
  LegendComponent,
  TooltipComponent,
} from "echarts/components";
import * as echarts from "echarts/core";
import { chartTheme } from "@/lib/chart-theme";

type LineChartPoint = {
  label: string;
  value: number;
  comparison?: number | null;
};

type LineChartProps = {
  points?: LineChartPoint[];
  title?: string;
  detailLabel?: string;
};

const defaultPoints: LineChartPoint[] = [
  { label: "Mon", value: 18, comparison: 16 },
  { label: "Tue", value: 26, comparison: 19 },
  { label: "Wed", value: 21, comparison: 22 },
  { label: "Thu", value: 34, comparison: 29 },
  { label: "Fri", value: 29, comparison: 27 },
];

echarts.use([
  CanvasRenderer,
  EChartsLineChart,
  GridComponent,
  LegendComponent,
  TooltipComponent,
]);

export function LineChart({
  points = defaultPoints,
  title = "Trend",
  detailLabel = "sample data",
}: LineChartProps) {
  const option = useMemo(
    () => ({
      animationDuration: 200,
      color: [chartTheme.line, chartTheme.comparison],
      grid: {
        top: 24,
        right: 16,
        bottom: 24,
        left: 16,
        containLabel: true,
      },
      legend: {
        bottom: 0,
        icon: "circle",
        itemHeight: 8,
        itemWidth: 8,
        textStyle: {
          color: chartTheme.label,
          fontFamily: "IBM Plex Sans",
        },
      },
      tooltip: {
        trigger: "axis",
        backgroundColor: chartTheme.tooltipBackground,
        borderColor: chartTheme.grid,
        textStyle: {
          color: chartTheme.tooltipText,
          fontFamily: "IBM Plex Sans",
        },
      },
      xAxis: {
        type: "category",
        data: points.map((point) => point.label),
        axisLine: {
          lineStyle: {
            color: chartTheme.grid,
          },
        },
        axisTick: {
          show: false,
        },
        axisLabel: {
          color: chartTheme.label,
          fontFamily: "IBM Plex Sans",
        },
      },
      yAxis: {
        type: "value",
        splitNumber: 4,
        axisLine: {
          show: false,
        },
        axisTick: {
          show: false,
        },
        axisLabel: {
          color: chartTheme.label,
          fontFamily: "IBM Plex Mono",
        },
        splitLine: {
          lineStyle: {
            color: chartTheme.grid,
          },
        },
      },
      series: [
        {
          name: "Volume",
          type: "line",
          data: points.map((point) => point.value),
          smooth: false,
          symbolSize: 6,
          lineStyle: {
            width: 2,
          },
        },
        ...(points.some((point) => point.comparison !== undefined)
          ? [
              {
                name: "Comparison",
                type: "line",
                data: points.map((point) => point.comparison ?? null),
                smooth: false,
                symbolSize: 5,
                lineStyle: {
                  type: "dashed",
                  width: 2,
                },
              },
            ]
          : []),
      ],
    }),
    [points],
  );

  return (
    <div className="surface-panel p-5">
      <div className="flex items-baseline justify-between gap-3">
        <h3 className="section-title">{title}</h3>
        <span className="mono text-xs text-text-muted">{detailLabel}</span>
      </div>
      <ReactEChartsCore
        echarts={echarts}
        option={option}
        notMerge
        lazyUpdate
        opts={{ renderer: "canvas" }}
        style={{ height: 260, width: "100%", marginTop: 16 }}
      />
    </div>
  );
}
