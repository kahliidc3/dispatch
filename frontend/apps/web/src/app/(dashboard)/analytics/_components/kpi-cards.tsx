const metrics = [
  { label: "Sends today", value: "18,240" },
  { label: "Bounce rate", value: "0.42%" },
  { label: "Complaint rate", value: "0.01%" },
  { label: "Open rate", value: "37.8%" },
];

export function KpiCards() {
  return (
    <section className="surface-panel p-6">
      <div className="page-stack">
        <div>
          <h2 className="section-title">Summary</h2>
          <p className="page-description">
            Placeholder analytics values based on static data.
          </p>
        </div>
        <div className="grid gap-4 md:grid-cols-2">
          {metrics.map((metric) => (
            <div key={metric.label} className="surface-panel-muted p-4">
              <p className="text-sm text-text-muted">{metric.label}</p>
              <p className="mt-2 text-xl font-semibold tracking-[-0.02em]">
                {metric.value}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
