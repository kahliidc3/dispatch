import { SuppressionTable } from "./_components/suppression-table";

export default function SuppressionPage() {
  return (
    <div className="page-stack">
      <header className="page-header">
        <div>
          <h1 className="page-title">Suppression</h1>
          <p className="page-description">
            Platform-wide suppression actions and audit flows are deferred. This
            page reserves the route and table surface.
          </p>
        </div>
      </header>
      <SuppressionTable />
    </div>
  );
}
