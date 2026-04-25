export type Template = {
  id: string;
  name: string;
  description: string | null;
  activeVersion: number | null;
  createdAt: string;
  updatedAt: string;
};

export type TemplateVersion = {
  id: string;
  templateId: string;
  version: number;
  subject: string;
  bodyText: string;
  bodyHtml: string;
  publishedAt: string | null;
  createdAt: string;
};

export type MergeTag = {
  tag: string;
  label: string;
};
