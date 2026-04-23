import { PreviewPane } from "../_components/preview-pane";
import { TemplateEditor } from "../_components/template-editor";

type TemplateDetailPageProps = {
  params: Promise<{ templateId: string }>;
};

export default async function TemplateDetailPage({
  params,
}: TemplateDetailPageProps) {
  const { templateId } = await params;

  return (
    <div className="page-stack">
      <header className="page-header">
        <div>
          <h1 className="page-title">Template detail</h1>
          <p className="page-description">
            Editing and preview panes are scaffolded for <span className="mono">{templateId}</span>.
          </p>
        </div>
      </header>
      <div className="grid gap-4 xl:grid-cols-[minmax(0,1.2fr)_minmax(0,0.8fr)]">
        <TemplateEditor />
        <PreviewPane />
      </div>
    </div>
  );
}
