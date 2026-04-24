import type { UserRole } from "@/types/api";

export type NavigationItem = {
  href: string;
  label: string;
  description: string;
  keywords: string[];
  roles?: UserRole[];
};

export type NavigationSection = {
  title: string;
  items: NavigationItem[];
};

const dashboardNavigation: NavigationSection[] = [
  {
    title: "Campaigns",
    items: [
      {
        href: "/",
        label: "Overview",
        description: "Shell baseline, route coverage, and Sprint status.",
        keywords: ["home", "dashboard", "overview"],
      },
      {
        href: "/campaigns",
        label: "Campaigns",
        description: "Browse campaign placeholders and drill into detail views.",
        keywords: ["launch", "monitoring", "messages"],
      },
      {
        href: "/templates",
        label: "Templates",
        description: "Reserve template list and editor routes for later sprints.",
        keywords: ["editor", "versions", "preview"],
      },
    ],
  },
  {
    title: "Audience",
    items: [
      {
        href: "/contacts",
        label: "Contacts",
        description: "Browse, filter, and manage contacts with lifecycle controls and list membership.",
        keywords: ["lists", "segments", "import", "unsubscribe"],
      },
      {
        href: "/lists",
        label: "Lists",
        description: "Create and manage contact lists for targeted campaign sends.",
        keywords: ["groups", "segments", "contacts", "membership"],
      },
      {
        href: "/segments",
        label: "Segments",
        description: "Build query-based audiences with a visual predicate builder.",
        keywords: ["filter", "dsl", "audience", "query", "builder"],
      },
      {
        href: "/suppression",
        label: "Suppression",
        description: "Review suppression state and lifecycle placeholders.",
        keywords: ["unsubscribe", "complaints", "bounces"],
      },
    ],
  },
  {
    title: "Delivery",
    items: [
      {
        href: "/domains",
        label: "Domains",
        description: "Add domains, verify DNS records, and manage domain lifecycle.",
        keywords: ["dns", "health", "warmup", "breaker", "verify"],
      },
      {
        href: "/sender-profiles",
        label: "Sender profiles",
        description: "From addresses and display names bound to verified domains.",
        keywords: ["from", "email", "sender", "profile", "ip pool"],
      },
      {
        href: "/analytics",
        label: "Analytics",
        description: "Overview metrics, charts, and deliverability views.",
        keywords: ["reputation", "metrics", "charts"],
      },
      {
        href: "/analytics/reputation",
        label: "Reputation",
        description: "Domain reputation placeholder route.",
        keywords: ["analytics", "postmaster", "deliverability"],
      },
    ],
  },
  {
    title: "Ops",
    items: [
      {
        href: "/ops/queues",
        label: "Queues",
        description: "Per-domain send queue depths, worker counts, and denial rates.",
        keywords: ["throttle", "queue", "worker", "celery", "backlog"],
        roles: ["admin"],
      },
    ],
  },
  {
    title: "Admin",
    items: [
      {
        href: "/settings",
        label: "Settings",
        description: "Platform settings shell and shared operator controls.",
        keywords: ["users", "keys", "settings"],
      },
      {
        href: "/settings/users",
        label: "Users",
        description: "User management placeholders.",
        keywords: ["admin", "accounts", "roles"],
        roles: ["admin"],
      },
      {
        href: "/settings/api-keys",
        label: "API Keys",
        description: "API key list and rotation placeholder route.",
        keywords: ["tokens", "auth", "credentials"],
        roles: ["admin"],
      },
    ],
  },
];

export function getDashboardNavigation(role: UserRole) {
  return dashboardNavigation.map((section) => ({
    ...section,
    items: section.items.filter(
      (item) => !item.roles || item.roles.includes(role),
    ),
  }));
}

export function getCommandPaletteItems(role: UserRole) {
  return getDashboardNavigation(role).flatMap((section) =>
    section.items.map((item) => ({
      ...item,
      section: section.title,
      searchText: [
        item.label,
        item.description,
        section.title,
        ...item.keywords,
      ]
        .join(" ")
        .toLowerCase(),
    })),
  );
}
