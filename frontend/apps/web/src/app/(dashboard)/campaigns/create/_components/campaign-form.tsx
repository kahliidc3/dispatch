import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export function CampaignForm() {
  return (
    <section className="surface-panel p-6">
      <div className="grid gap-5">
        <div>
          <label className="label" htmlFor="campaign-name">
            Campaign name
          </label>
          <Input id="campaign-name" placeholder="Q2 operator seed run" />
        </div>
        <div>
          <label className="label" htmlFor="campaign-sender">
            Sender profile
          </label>
          <select id="campaign-sender" className="field" defaultValue="">
            <option value="" disabled>
              Select sender profile
            </option>
            <option>ops@m47.dispatch.internal</option>
          </select>
        </div>
        <div>
          <label className="label" htmlFor="campaign-template">
            Template version
          </label>
          <select id="campaign-template" className="field" defaultValue="">
            <option value="" disabled>
              Select template version
            </option>
            <option>Warmup sequence v1</option>
          </select>
        </div>
        <div className="flex flex-wrap gap-3">
          <Button type="button">Save draft</Button>
          <Button type="button" variant="outline">
            Audience step later
          </Button>
        </div>
      </div>
    </section>
  );
}
