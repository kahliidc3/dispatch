import { SectionPanel } from "@/components/patterns/section-panel";
import { getQueueSnapshot } from "@/app/(dashboard)/ops/_lib/ops-queries";
import { QueuesViewer } from "./_components/queues-viewer";

export default function QueuesPage() {
  const rows = getQueueSnapshot();

  return (
    <div className="page-stack">
      <header className="page-header">
        <div>
          <h1 className="page-title">Queues</h1>
          <p className="page-description">
            Per-domain send queue depth, worker counts, and denial rates.
          </p>
        </div>
      </header>

      <SectionPanel>
        <QueuesViewer initialRows={rows} />
      </SectionPanel>
    </div>
  );
}
