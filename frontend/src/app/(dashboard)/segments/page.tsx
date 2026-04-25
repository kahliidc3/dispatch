import { SegmentsManager } from "./_components/segments-manager";
import { mockSegments } from "./_lib/segments-queries";

export default function SegmentsPage() {
  return (
    <div className="page-stack">
      <header className="page-intro">
        <div className="page-intro-copy">
          <h1 className="page-title">Segments</h1>
          <p className="page-description">
            Build query-based audiences with a visual predicate builder. Segments
            are evaluated at campaign launch and frozen into immutable snapshots.
          </p>
        </div>
      </header>

      <SegmentsManager initialSegments={mockSegments} />
    </div>
  );
}
