import Link from "next/link";
import { notFound } from "next/navigation";
import { TemplateWorkspace } from "../_components/template-workspace";
import {
  getTemplateById,
  getVersionsForTemplate,
  mockMergeTags,
} from "../_lib/templates-queries";

type TemplateDetailPageProps = {
  params: Promise<{ templateId: string }>;
};

export default async function TemplateDetailPage({
  params,
}: TemplateDetailPageProps) {
  const { templateId } = await params;

  const template = getTemplateById(templateId);
  if (!template) notFound();

  const versions = getVersionsForTemplate(templateId);

  return (
    <div className="page-stack">
      <nav
        className="flex items-center gap-2 text-sm text-text-muted"
        aria-label="Breadcrumb"
      >
        <Link href="/templates" className="hover:underline">
          Templates
        </Link>
        <span aria-hidden="true">/</span>
        <span>{template.name}</span>
      </nav>

      <header className="page-intro">
        <div className="page-intro-copy">
          <h1 className="page-title">{template.name}</h1>
          {template.description ? (
            <p className="page-description">{template.description}</p>
          ) : null}
        </div>
      </header>

      <TemplateWorkspace
        template={template}
        versions={versions}
        mergeTags={mockMergeTags}
      />
    </div>
  );
}
