import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export function CampaignsFilters() {
  return (
    <section className="surface-panel p-5">
      <div className="grid gap-4 md:grid-cols-[1fr_auto_auto]">
        <div>
          <label className="label" htmlFor="campaign-search">
            Search
          </label>
          <Input
            id="campaign-search"
            placeholder="Campaign name, status, or audience"
          />
        </div>
        <div className="flex items-end">
          <Button type="button" variant="outline">
            Filters later
          </Button>
        </div>
        <div className="flex items-end">
          <Button asChild>
            <Link href="/campaigns/create">Create draft</Link>
          </Button>
        </div>
      </div>
    </section>
  );
}
