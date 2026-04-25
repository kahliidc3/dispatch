import { SectionPanel } from "@/components/patterns/section-panel";
import { getBreakerMatrix } from "@/app/(dashboard)/ops/_lib/ops-queries";
import { BreakerConsole } from "./_components/breaker-console";

export default function CircuitBreakersPage() {
  const entries = getBreakerMatrix();

  return (
    <div className="page-stack">
      <header className="page-header">
        <div>
          <h1 className="page-title">Circuit breakers</h1>
          <p className="page-description">
            Four-scope breaker matrix. Polls every 10 seconds. Resets require a
            typed justification.
          </p>
        </div>
      </header>

      <SectionPanel>
        <BreakerConsole initialEntries={entries} />
      </SectionPanel>
    </div>
  );
}
