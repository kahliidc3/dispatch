import Link from "next/link";
import { DataTable } from "@/components/shared/data-table";

const templates = [
  { id: "tpl-001", name: "Warmup plain text", version: "v1" },
  { id: "tpl-002", name: "Seed inbox check", version: "v3" },
];

export default function TemplatesPage() {
  return (
    <div className="page-stack">
      <header className="page-header">
        <div>
          <h1 className="page-title">Templates</h1>
          <p className="page-description">
            Template authoring and immutable versioning are deferred. The
            scaffold locks the list and detail routes now.
          </p>
        </div>
      </header>
      <DataTable
        caption="Template list placeholder"
        columns={[
          { key: "name", label: "Template" },
          { key: "version", label: "Active version" },
        ]}
        rows={templates.map((template) => ({
          name: (
            <Link
              href={`/templates/${template.id}`}
              className="font-medium hover:underline"
            >
              {template.name}
            </Link>
          ),
          version: template.version,
        }))}
      />
    </div>
  );
}
