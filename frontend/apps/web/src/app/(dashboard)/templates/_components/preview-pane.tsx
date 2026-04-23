export function PreviewPane() {
  return (
    <section className="surface-panel p-6">
      <div className="page-stack">
        <div>
          <h2 className="section-title">Preview</h2>
          <p className="page-description">
            Split-pane preview, sample payload editing, and version diffing are
            deferred to Sprint 06.
          </p>
        </div>
        <div className="surface-panel-muted p-5">
          <p className="text-sm font-medium">Example email</p>
          <div className="mt-4 grid gap-3 text-sm text-text-muted">
            <p>Subject: Warm intro for Avery</p>
            <p>Hello Avery,</p>
            <p>This placeholder reserves the preview area for template work.</p>
          </div>
        </div>
      </div>
    </section>
  );
}
