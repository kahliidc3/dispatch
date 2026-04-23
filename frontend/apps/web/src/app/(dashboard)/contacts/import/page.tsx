import { EmptyState } from "@/components/shared/empty-state";

export default function ContactImportPage() {
  return (
    <div className="page-stack">
      <header className="page-header">
        <div>
          <h1 className="page-title">Import contacts</h1>
          <p className="page-description">
            The CSV wizard lands in Sprint 05. This page reserves the route and
            the onboarding surface for upload and validation work.
          </p>
        </div>
      </header>
      <EmptyState
        title="Import wizard placeholder"
        description="Upload, mapping, progress, and rejection review are deferred until the import pipeline is implemented."
      />
    </div>
  );
}
