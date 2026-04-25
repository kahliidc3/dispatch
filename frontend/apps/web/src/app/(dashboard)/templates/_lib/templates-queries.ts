import type { Template, TemplateVersion, MergeTag } from "@/types/template";

export const mockTemplates: Template[] = [
  {
    id: "tpl-001",
    name: "Warmup plain text",
    description: "Simple plain-text warmup email",
    activeVersion: 2,
    createdAt: "2026-01-10T09:00:00Z",
    updatedAt: "2026-03-15T14:22:00Z",
  },
  {
    id: "tpl-002",
    name: "Seed inbox check",
    description: null,
    activeVersion: 3,
    createdAt: "2026-01-12T11:00:00Z",
    updatedAt: "2026-04-01T08:45:00Z",
  },
  {
    id: "tpl-003",
    name: "Product update announcement",
    description: "Monthly product update newsletter",
    activeVersion: 1,
    createdAt: "2026-02-01T10:00:00Z",
    updatedAt: "2026-02-01T10:00:00Z",
  },
];

export const mockTemplateVersions: Record<string, TemplateVersion[]> = {
  "tpl-001": [
    {
      id: "tv-001-1",
      templateId: "tpl-001",
      version: 1,
      subject: "Hi {{first_name}}",
      bodyText: "Hi {{first_name}},\n\nJust checking in.\n\nBest,\nThe Team",
      bodyHtml:
        "<p>Hi {{first_name}},</p><p>Just checking in.</p><p>Best,<br>The Team</p>",
      publishedAt: "2026-01-10T10:00:00Z",
      createdAt: "2026-01-10T09:00:00Z",
    },
    {
      id: "tv-001-2",
      templateId: "tpl-001",
      version: 2,
      subject: "Quick check-in, {{first_name}}",
      bodyText:
        "Hi {{first_name}},\n\nJust wanted to touch base. Hope everything is going well!\n\nBest,\nThe Team",
      bodyHtml:
        "<p>Hi {{first_name}},</p><p>Just wanted to touch base. Hope everything is going well!</p><p>Best,<br>The Team</p>",
      publishedAt: "2026-03-15T14:22:00Z",
      createdAt: "2026-03-15T14:00:00Z",
    },
  ],
  "tpl-002": [
    {
      id: "tv-002-1",
      templateId: "tpl-002",
      version: 1,
      subject: "Test delivery for {{email}}",
      bodyText: "This is a seed check for {{email}}.",
      bodyHtml: "<p>This is a seed check for {{email}}.</p>",
      publishedAt: "2026-01-12T12:00:00Z",
      createdAt: "2026-01-12T11:00:00Z",
    },
    {
      id: "tv-002-2",
      templateId: "tpl-002",
      version: 2,
      subject: "Inbox seeding — {{email}}",
      bodyText: "Delivery verification for {{email}}. No action needed.",
      bodyHtml:
        "<p>Delivery verification for {{email}}. No action needed.</p>",
      publishedAt: "2026-02-20T10:00:00Z",
      createdAt: "2026-02-20T09:30:00Z",
    },
    {
      id: "tv-002-3",
      templateId: "tpl-002",
      version: 3,
      subject: "Inbox seed — v3",
      bodyText:
        "Delivery verification for {{email}}. Sent from {{sender_name}}. No action needed.",
      bodyHtml:
        "<p>Delivery verification for {{email}}. Sent from {{sender_name}}. No action needed.</p>",
      publishedAt: "2026-04-01T08:45:00Z",
      createdAt: "2026-04-01T08:00:00Z",
    },
  ],
  "tpl-003": [
    {
      id: "tv-003-1",
      templateId: "tpl-003",
      version: 1,
      subject: "Product update — {{month}}",
      bodyText:
        "Hi {{first_name}},\n\nHere's what's new this month:\n\n- Feature A\n- Feature B\n\nCheers,\nThe Team",
      bodyHtml:
        "<p>Hi {{first_name}},</p><p>Here's what's new this month:</p><ul><li>Feature A</li><li>Feature B</li></ul><p>Cheers,<br>The Team</p>",
      publishedAt: "2026-02-01T10:00:00Z",
      createdAt: "2026-02-01T10:00:00Z",
    },
  ],
};

export const mockMergeTags: MergeTag[] = [
  { tag: "{{first_name}}", label: "First name" },
  { tag: "{{last_name}}", label: "Last name" },
  { tag: "{{email}}", label: "Email address" },
  { tag: "{{sender_name}}", label: "Sender name" },
  { tag: "{{unsubscribe_url}}", label: "Unsubscribe URL" },
];

export function getTemplateById(id: string): Template | undefined {
  return mockTemplates.find((t) => t.id === id);
}

export function getVersionsForTemplate(templateId: string): TemplateVersion[] {
  return mockTemplateVersions[templateId] ?? [];
}
