import { chartTheme } from "@/lib/chart-theme";

type HeatmapProps = {
  cells?: number[][];
};

const defaultCells = [
  [1, 2, 3, 2, 1],
  [2, 3, 4, 3, 2],
  [1, 2, 4, 2, 1],
  [0, 1, 2, 1, 0],
];

function cellColor(value: number) {
  return chartTheme.heatmap(value);
}

export function Heatmap({ cells = defaultCells }: HeatmapProps) {
  return (
    <div className="surface-panel p-5">
      <div className="flex items-baseline justify-between gap-3">
        <h3 className="section-title">Heatmap placeholder</h3>
        <span className="mono text-xs text-text-muted">static sample</span>
      </div>
      <div
        className="mt-4 grid gap-2"
        style={{
          gridTemplateColumns: `repeat(${cells[0]?.length ?? 0}, minmax(0, 1fr))`,
        }}
      >
        {cells.flatMap((row, rowIndex) =>
          row.map((value, columnIndex) => (
            <div
              key={`${rowIndex}-${columnIndex}`}
              className="aspect-square rounded-[8px] border border-border"
              style={{ background: cellColor(value) }}
            />
          )),
        )}
      </div>
    </div>
  );
}
