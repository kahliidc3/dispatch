import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export function TemplateEditor() {
  return (
    <section className="surface-panel p-6">
      <div className="grid gap-5">
        <div>
          <label className="label" htmlFor="template-subject">
            Subject
          </label>
          <Input
            id="template-subject"
            placeholder="Warm intro for {{first_name}}"
          />
        </div>
        <div>
          <label className="label" htmlFor="template-body">
            Body
          </label>
          <textarea
            id="template-body"
            className="field min-h-48"
            placeholder="Plain-text template body placeholder"
          />
        </div>
        <div className="flex flex-wrap gap-3">
          <Button type="button">Save draft</Button>
          <Button type="button" variant="outline">
            Version history later
          </Button>
        </div>
      </div>
    </section>
  );
}
