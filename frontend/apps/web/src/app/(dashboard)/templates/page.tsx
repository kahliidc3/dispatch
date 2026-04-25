import Link from "next/link";
import { TemplatesManager } from "./_components/templates-manager";
import { mockTemplates } from "./_lib/templates-queries";

export default function TemplatesPage() {
  return (
    <div className="page-stack">
      <header className="page-intro">
        <div className="page-intro-copy">
          <h1 className="page-title">Templates</h1>
          <p className="page-description">
            Author and version email templates. Each save creates an immutable
            version — nothing is ever overwritten.
          </p>
        </div>
        <div className="page-actions">
          <TemplatesManager />
        </div>
      </header>

      <div className="surface-panel overflow-hidden">
        <table className="w-full text-sm" aria-label="Template list">
          <thead>
            <tr className="border-b border-border">
              <th className="px-4 py-3 text-left font-medium text-text-muted">
                Name
              </th>
              <th className="px-4 py-3 text-left font-medium text-text-muted">
                Active version
              </th>
              <th className="px-4 py-3 text-left font-medium text-text-muted">
                Last updated
              </th>
            </tr>
          </thead>
          <tbody>
            {mockTemplates.map((template) => (
              <tr
                key={template.id}
                className="border-b border-border last:border-0 hover:bg-surface-muted/50 transition-colors"
              >
                <td className="px-4 py-3">
                  <Link
                    href={`/templates/${template.id}`}
                    className="font-medium hover:underline underline-offset-2"
                  >
                    {template.name}
                  </Link>
                  {template.description ? (
                    <p className="text-xs text-text-muted mt-0.5">
                      {template.description}
                    </p>
                  ) : null}
                </td>
                <td className="px-4 py-3 mono text-xs">
                  {template.activeVersion != null
                    ? `v${template.activeVersion}`
                    : <span className="text-text-muted">No versions</span>}
                </td>
                <td className="px-4 py-3 text-text-muted text-xs">
                  {new Intl.DateTimeFormat("en-US", {
                    dateStyle: "medium",
                  }).format(new Date(template.updatedAt))}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
