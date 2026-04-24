import Link from "next/link";
import { PageIntro } from "@/components/patterns/page-intro";
import { PropertiesList } from "@/components/patterns/properties-list";
import { SectionPanel } from "@/components/patterns/section-panel";
import { Badge } from "@/components/ui/badge";
import { DataTable } from "@/components/shared/data-table";

const routeRows = [
  { surface: "Overview", path: "/", status: "Protected" },
  { surface: "Login", path: "/login", status: "Open" },
  { surface: "Campaigns", path: "/campaigns", status: "Protected" },
  { surface: "Contacts", path: "/contacts", status: "Protected" },
  { surface: "Domains", path: "/domains", status: "Protected" },
  { surface: "Templates", path: "/templates", status: "Protected" },
  { surface: "Analytics", path: "/analytics", status: "Protected" },
  { surface: "Suppression", path: "/suppression", status: "Protected" },
  { surface: "Settings", path: "/settings", status: "Protected" },
];

export default function DashboardHomePage() {
  return (
    <div className="page-stack">
      <PageIntro
        title="Dispatch"
        description="Sprint 01 turns the scaffold into a protected operator shell with typed request helpers, session gating, and reusable frontend primitives for the next feature sprints."
        actions={<Badge variant="outline">Core shell foundation</Badge>}
      />

      <SectionPanel
        title="What ships in Sprint 01"
        description="Signed local session handling, typed API helpers, keyboard navigation, production-grade shared primitives, and the first protected version of the dashboard shell."
      >
        <PropertiesList
          items={[
            { label: "Backend coupling", value: "Frontend-contained only" },
            { label: "Shared root tooling", value: "Deferred" },
            { label: "Auth boundary", value: "Protected shell via local session" },
          ]}
        />
      </SectionPanel>

      <section className="page-stack">
        <div>
          <h2 className="section-title">Route inventory</h2>
          <p className="page-description">
            Every row below resolves inside the protected shell, except the
            dedicated login route.
          </p>
        </div>
        <DataTable
          caption="Sprint 01 route coverage"
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
            status: (
              <Badge
                variant={route.status === "Open" ? "outline" : "success"}
              >
                {route.status}
              </Badge>
            ),
          }))}
        />
      </section>
    </div>
  );
}
