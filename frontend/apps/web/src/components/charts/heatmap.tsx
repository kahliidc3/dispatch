"use client";

import { useMemo } from "react";
import ReactEChartsCore from "echarts-for-react/lib/core";
import { CanvasRenderer } from "echarts/renderers";
import { HeatmapChart as EChartsHeatmapChart } from "echarts/charts";
import {
  GridComponent,
  TooltipComponent,
  VisualMapComponent,
} from "echarts/components";
import * as echarts from "echarts/core";
import { chartTheme } from "@/lib/chart-theme";

type HeatmapProps = {
  cells?: number[][];
  title?: string;
  detailLabel?: string;
};

const defaultCells = [
  [1, 2, 3, 2, 1],
  [2, 3, 4, 3, 2],
  [1, 2, 4, 2, 1],
  [0, 1, 2, 1, 0],
];

const defaultColumns = ["Mon", "Tue", "Wed", "Thu", "Fri"];
const defaultRows = ["Core", "Growth", "Warmup", "Risk"];

echarts.use([
  CanvasRenderer,
  EChartsHeatmapChart,
  GridComponent,
  TooltipComponent,
  VisualMapComponent,
]);

export function Heatmap({
  cells = defaultCells,
  title = "Heatmap",
  detailLabel = "sample data",
}: HeatmapProps) {
  const option = useMemo(
    () => ({
      animationDuration: 200,
      grid: {
        top: 16,
        right: 16,
        bottom: 24,
        left: 72,
      },
      tooltip: {
        position: "top",
        backgroundColor: chartTheme.tooltipBackground,
        borderColor: chartTheme.grid,
        textStyle: {
          color: chartTheme.tooltipText,
          fontFamily: "IBM Plex Sans",
        },
      },
      xAxis: {
        type: "category",
        data: defaultColumns.slice(0, cells[0]?.length ?? defaultColumns.length),
        splitArea: {
          show: false,
        },
        axisLine: {
          lineStyle: {
            color: chartTheme.grid,
          },
        },
        axisLabel: {
          color: chartTheme.label,
          fontFamily: "IBM Plex Sans",
        },
      },
      yAxis: {
        type: "category",
        data: defaultRows.slice(0, cells.length),
        axisLine: {
          show: false,
        },
        axisTick: {
          show: false,
        },
        axisLabel: {
          color: chartTheme.label,
          fontFamily: "IBM Plex Sans",
        },
      },
      visualMap: {
        show: false,
        min: 0,
        max: 4,
        inRange: {
          color: chartTheme.heatmapScale,
        },
      },
      series: [
        {
          type: "heatmap",
          data: cells.flatMap((row, rowIndex) =>
            row.map((value, columnIndex) => [columnIndex, rowIndex, value]),
          ),
          label: {
            show: true,
            color: chartTheme.tooltipText,
            fontFamily: "IBM Plex Mono",
            fontSize: 11,
          },
          emphasis: {
            itemStyle: {
              borderColor: chartTheme.grid,
              borderWidth: 1,
            },
          },
        },
      ],
    }),
    [cells],
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
