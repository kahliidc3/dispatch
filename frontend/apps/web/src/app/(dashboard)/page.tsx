import Link from "next/link";
import { PageIntro } from "@/components/patterns/page-intro";
import { PropertiesList } from "@/components/patterns/properties-list";
import { SectionPanel } from "@/components/patterns/section-panel";
import { Badge } from "@/components/ui/badge";
import { DataTable } from "@/components/shared/data-table";

const routeRows = [
  { surface: "Overview", path: "/", status: "Ready" },
  { surface: "Login", path: "/login", status: "Ready" },
  { surface: "Campaigns", path: "/campaigns", status: "Ready" },
  { surface: "Contacts", path: "/contacts", status: "Ready" },
  { surface: "Domains", path: "/domains", status: "Ready" },
  { surface: "Templates", path: "/templates", status: "Ready" },
  { surface: "Analytics", path: "/analytics", status: "Ready" },
  { surface: "Suppression", path: "/suppression", status: "Ready" },
  { surface: "Settings", path: "/settings", status: "Ready" },
];

export default function DashboardHomePage() {
  return (
    <div className="page-stack">
      <PageIntro
        title="Dispatch"
        description="Frontend bootstrap is active under frontend/apps/web. This route locks the App Router shell and the placeholder surface inventory before feature work starts."
        actions={<Badge variant="outline">Docs-first scaffold</Badge>}
      />

      <SectionPanel
        title="What ships in Sprint 00"
        description="Next.js 16 app bootstrap, route groups, restrained tokens, baseline primitives, local test tooling, and placeholder routes for the documented dashboard areas."
      >
        <PropertiesList
          items={[
            { label: "Backend coupling", value: "None in this sprint" },
            { label: "Shared root tooling", value: "Deferred" },
            { label: "Visual baseline", value: "HVA-aligned operator UI" },
          ]}
        />
      </SectionPanel>

      <section className="page-stack">
        <div>
          <h2 className="section-title">Route inventory</h2>
          <p className="page-description">
            Every row below resolves to a placeholder surface in the current
            scaffold.
          </p>
        </div>
        <DataTable
          caption="Sprint 00 route coverage"
          columns={[
            { key: "surface", label: "Surface" },
            { key: "path", label: "Path", className: "mono text-xs" },
            { key: "status", label: "Status" },
          ]}
          rows={routeRows.map((route) => ({
            surface: (
              <Link href={route.path} className="font-medium hover:underline">
                {route.surface}
              </Link>
            ),
            path: route.path,
            status: <Badge variant="outline">{route.status}</Badge>,
          }))}
        />
      </section>
    </div>
  );
}
