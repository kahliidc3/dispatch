import { Badge } from "@/components/ui/badge";
import { formatTimestamp, maskEmailAddress } from "@/lib/formatters";
import type { ContactRecord } from "@/types/contact";

const lifecycleVariant = {
  active: "success",
  suppressed: "danger",
  unsubscribed: "warning",
  bounced: "muted",
} as const;

type ContactDrawerProps = {
  contact: ContactRecord;
};

export function ContactDrawer({ contact }: ContactDrawerProps) {
  return (
    <section className="surface-panel p-6">
      <div className="page-stack">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h2 className="section-title">{maskEmailAddress(contact.email)}</h2>
            <p className="page-description">
              Detail drawer behavior lands in Sprint 04. This static panel
              locks the route and content groupings.
            </p>
          </div>
          <Badge variant={lifecycleVariant[contact.lifecycle]}>
            {contact.lifecycle}
          </Badge>
        </div>
        <div className="summary-list">
          <div className="summary-row">
            <span className="text-sm font-medium">Contact id</span>
            <span className="mono text-sm text-text-muted">{contact.id}</span>
          </div>
          <div className="summary-row">
            <span className="text-sm font-medium">Source</span>
            <span className="text-sm text-text-muted">{contact.source}</span>
          </div>
          <div className="summary-row">
            <span className="text-sm font-medium">Last updated</span>
            <span className="text-sm text-text-muted">
              {formatTimestamp(contact.updatedAt)}
            </span>
          </div>
        </div>
      </div>
    </section>
  );
}
