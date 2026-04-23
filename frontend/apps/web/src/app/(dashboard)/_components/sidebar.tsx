import Link from "next/link";
import { env } from "@/lib/env";

const navigation = [
  { href: "/", label: "Overview" },
  { href: "/campaigns", label: "Campaigns" },
  { href: "/contacts", label: "Contacts" },
  { href: "/domains", label: "Domains" },
  { href: "/templates", label: "Templates" },
  { href: "/analytics", label: "Analytics" },
  { href: "/suppression", label: "Suppression" },
  { href: "/settings", label: "Settings" },
];

export function Sidebar() {
  return (
    <aside className="app-rail">
      <div className="grid gap-1">
        <Link href="/" className="text-lg font-semibold tracking-[-0.02em]">
          {env.NEXT_PUBLIC_APP_NAME}
        </Link>
        <p className="text-sm text-text-muted">Sprint 00 bootstrap</p>
      </div>
      <nav className="grid gap-1" aria-label="Primary">
        {navigation.map((item) => (
          <Link key={item.href} href={item.href} className="rail-link">
            {item.label}
          </Link>
        ))}
      </nav>
      <div className="surface-panel-muted p-4">
        <p className="text-sm font-medium">Current scope</p>
        <p className="mt-2 text-sm text-text-muted">
          Route tree, local tooling, tokens, and placeholder surfaces only.
        </p>
      </div>
    </aside>
  );
}
