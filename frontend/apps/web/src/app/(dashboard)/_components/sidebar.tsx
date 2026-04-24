"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Badge } from "@/components/ui/badge";
import { publicEnv } from "@/lib/env";
import { getDashboardNavigation } from "@/lib/navigation";
import { cn } from "@/lib/utils";
import type { SessionUser } from "@/types/api";

type SidebarProps = {
  session: SessionUser;
};

function isActivePath(pathname: string, href: string) {
  if (href === "/") {
    return pathname === "/";
  }

  return pathname === href || pathname.startsWith(`${href}/`);
}

export function Sidebar({ session }: SidebarProps) {
  const pathname = usePathname();
  const navigation = getDashboardNavigation(session.role);

  return (
    <aside className="app-rail">
      <div className="grid gap-3">
        <div className="grid gap-1">
          <Link href="/" className="text-lg font-semibold tracking-[-0.02em]">
            {publicEnv.NEXT_PUBLIC_APP_NAME}
          </Link>
          <p className="text-sm text-text-muted">Operator workspace</p>
        </div>
        <div className="surface-panel-muted grid gap-3 p-4">
          <div className="flex flex-wrap items-center gap-2">
            <p className="text-sm font-medium">{session.name}</p>
            <Badge variant="outline">{session.role}</Badge>
          </div>
          <p className="text-sm text-text-muted">{session.email}</p>
        </div>
      </div>
      <nav className="grid gap-4" aria-label="Primary">
        {navigation.map((section) => (
          <div key={section.title} className="grid gap-1.5">
            <p className="px-3 text-sm font-medium text-text-muted">
              {section.title}
            </p>
            <div className="grid gap-1">
              {section.items.map((item) => {
                const active = isActivePath(pathname, item.href);

                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    aria-current={active ? "page" : undefined}
                    className={cn("rail-link", active && "rail-link-active")}
                  >
                    <span>{item.label}</span>
                  </Link>
                );
              })}
            </div>
          </div>
        ))}
      </nav>
      <div className="surface-panel-muted p-4">
        <p className="text-sm font-medium">Sprint 01 status</p>
        <p className="mt-2 text-sm text-text-muted">
          Core shell, typed request layer, and shared primitives are active.
        </p>
      </div>
    </aside>
  );
}
