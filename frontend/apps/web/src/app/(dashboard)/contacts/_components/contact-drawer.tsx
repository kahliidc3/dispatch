"use client";

import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { DataTable } from "@/components/shared/data-table";
import { formatTimestamp } from "@/lib/formatters";
import type {
  ContactDetail,
  ContactEventType,
  ContactLifecycle,
} from "@/types/contact";

const lifecycleBadge: Record<
  ContactLifecycle,
  "success" | "danger" | "warning" | "muted"
> = {
  active: "success",
  suppressed: "danger",
  complained: "danger",
  unsubscribed: "warning",
  bounced: "muted",
  deleted: "muted",
};

const eventBadge: Record<
  ContactEventType,
  "success" | "danger" | "warning" | "muted"
> = {
  sent: "muted",
  delivered: "success",
  opened: "success",
  clicked: "success",
  bounced: "danger",
  complained: "danger",
  unsubscribed: "warning",
};

type ContactDrawerProps = {
  contact: ContactDetail;
};

export function ContactDrawer({ contact }: ContactDrawerProps) {
  const displayName =
    [contact.firstName, contact.lastName].filter(Boolean).join(" ") || null;

  return (
    <section className="surface-panel">
      <div className="panel-header">
        <div className="panel-copy">
          <h2 className="panel-title">{contact.email}</h2>
          {displayName ? (
            <p className="panel-description">{displayName}</p>
          ) : null}
        </div>
        <Badge variant={lifecycleBadge[contact.lifecycle]}>
          {contact.lifecycle}
        </Badge>
      </div>
      <div className="px-6 pb-6">
        <Tabs defaultValue="overview">
          <TabsList>
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="lists">
              Lists ({contact.lists.length})
            </TabsTrigger>
            <TabsTrigger value="preferences">Preferences</TabsTrigger>
            <TabsTrigger value="history">
              History ({contact.recentEvents.length})
            </TabsTrigger>
          </TabsList>

          <TabsContent value="overview">
            <dl className="summary-list">
              <div className="summary-row">
                <dt className="text-sm font-medium">Contact ID</dt>
                <dd className="mono text-sm text-text-muted">{contact.id}</dd>
              </div>
              <div className="summary-row">
                <dt className="text-sm font-medium">Email</dt>
                <dd className="text-sm text-text-muted">{contact.email}</dd>
              </div>
              <div className="summary-row">
                <dt className="text-sm font-medium">Source</dt>
                <dd className="text-sm text-text-muted">
                  {contact.source.replace("_", " ")}
                </dd>
              </div>
              <div className="summary-row">
                <dt className="text-sm font-medium">Created</dt>
                <dd className="text-sm text-text-muted">
                  {formatTimestamp(contact.createdAt)}
                </dd>
              </div>
              <div className="summary-row">
                <dt className="text-sm font-medium">Last updated</dt>
                <dd className="text-sm text-text-muted">
                  {formatTimestamp(contact.updatedAt)}
                </dd>
              </div>
              {contact.suppressedAt ? (
                <div className="summary-row">
                  <dt className="text-sm font-medium">Suppressed at</dt>
                  <dd className="text-sm text-text-muted">
                    {formatTimestamp(contact.suppressedAt)}
                  </dd>
                </div>
              ) : null}
              {contact.suppressionReason ? (
                <div className="summary-row">
                  <dt className="text-sm font-medium">Suppression reason</dt>
                  <dd className="text-sm text-text-muted">
                    {contact.suppressionReason}
                  </dd>
                </div>
              ) : null}
            </dl>
          </TabsContent>

          <TabsContent value="lists">
            {contact.lists.length > 0 ? (
              <DataTable
                columns={[
                  { key: "name", label: "List" },
                  { key: "addedAt", label: "Added", className: "text-right" },
                ]}
                rows={contact.lists.map((l) => ({
                  name: l.listName,
                  addedAt: formatTimestamp(l.addedAt),
                }))}
              />
            ) : (
              <p className="py-6 text-sm text-text-muted">
                This contact is not in any lists.
              </p>
            )}
          </TabsContent>

          <TabsContent value="preferences">
            <ul className="divide-y divide-border" role="list">
              {contact.preferences.map((pref) => (
                <li
                  key={pref.key}
                  className="flex items-center justify-between py-3"
                >
                  <span className="text-sm font-medium">{pref.label}</span>
                  <Badge variant={pref.subscribed ? "success" : "muted"}>
                    {pref.subscribed ? "Subscribed" : "Unsubscribed"}
                  </Badge>
                </li>
              ))}
            </ul>
          </TabsContent>

          <TabsContent value="history">
            {contact.recentEvents.length > 0 ? (
              <ul className="divide-y divide-border" role="list">
                {contact.recentEvents.map((event) => (
                  <li
                    key={event.id}
                    className="flex flex-wrap items-start justify-between gap-3 py-3"
                  >
                    <div className="flex flex-wrap items-center gap-2">
                      <Badge variant={eventBadge[event.type]}>
                        {event.type}
                      </Badge>
                      {event.detail ? (
                        <span className="text-sm text-text-muted">
                          {event.detail}
                        </span>
                      ) : null}
                    </div>
                    <span className="text-sm text-text-muted">
                      {formatTimestamp(event.occurredAt)}
                    </span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="py-6 text-sm text-text-muted">
                No events recorded.
              </p>
            )}
          </TabsContent>
        </Tabs>
      </div>
    </section>
  );
}
