import { formatTimestamp } from "@/lib/formatters";
import { CommandPalette } from "./command-palette";

export function Topbar() {
  return (
    <header className="app-topbar">
      <div className="grid gap-0.5">
        <span className="text-sm font-medium">Frontend scaffold</span>
        <span className="text-xs text-text-muted">
          {formatTimestamp(new Date().toISOString())}
        </span>
      </div>
      <CommandPalette />
    </header>
  );
}
