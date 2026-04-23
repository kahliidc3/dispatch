import { Button } from "@/components/ui/button";

export function LaunchActions() {
  return (
    <section className="surface-panel p-6">
      <div className="page-stack">
        <div>
          <h2 className="section-title">Launch controls</h2>
          <p className="page-description">
            Review, gating, and launch confirmation are deferred to Sprint 09.
          </p>
        </div>
        <div className="flex flex-wrap gap-3">
          <Button type="button" variant="outline">
            Review placeholder
          </Button>
          <Button type="button" disabled>
            Launch disabled
          </Button>
        </div>
      </div>
    </section>
  );
}
