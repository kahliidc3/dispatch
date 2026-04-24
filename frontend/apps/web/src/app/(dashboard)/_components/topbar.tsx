import { Badge } from "@/components/ui/badge";
import { formatTimestamp } from "@/lib/formatters";
import type { SessionResponse, SessionUser } from "@/types/api";
import { CommandPalette } from "./command-palette";
import { SessionMenu } from "./session-menu";

type TopbarProps = {
  session: SessionUser;
  source: SessionResponse["source"];
};

export function Topbar({ session, source }: TopbarProps) {
  return (
    <header className="app-topbar">
      <div className="grid gap-1">
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-sm font-medium">Protected dashboard shell</span>
          <Badge variant="outline">
            {source === "dev" ? "Local session" : "Authenticated"}
          </Badge>
        </div>
        <span className="text-xs text-text-muted">
          {formatTimestamp(new Date().toISOString())}
        </span>
      </div>
      <div className="flex items-center gap-3">
        <CommandPalette role={session.role} />
        <SessionMenu session={session} source={source} />
      </div>
    </header>
  );
}
