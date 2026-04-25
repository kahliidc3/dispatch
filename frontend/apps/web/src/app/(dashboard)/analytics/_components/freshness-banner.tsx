type FreshnessBannerProps = {
  lastUpdatedAt: string;
  isStale: boolean;
};

export function FreshnessBanner({ lastUpdatedAt, isStale }: FreshnessBannerProps) {
  const formatted = new Date(lastUpdatedAt).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });

  if (isStale) {
    return (
      <div
        role="alert"
        className="rounded-lg border border-warning/40 bg-warning/10 px-4 py-2.5 text-sm text-warning flex items-center gap-2"
      >
        <span aria-hidden="true">⚠</span>
        Data may be stale — last updated at {formatted}. Metrics refresh every 5
        minutes.
      </div>
    );
  }

  return (
    <p className="text-xs text-text-muted">
      Last updated: {formatted}
    </p>
  );
}
