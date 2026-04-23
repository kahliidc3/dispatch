import Link from "next/link";
import { DataTable } from "@/components/shared/data-table";
import { Badge } from "@/components/ui/badge";
import { formatTimestamp, maskEmailAddress } from "@/lib/formatters";
import { contacts } from "../_lib/contacts-queries";

const lifecycleVariant = {
  active: "success",
  suppressed: "danger",
  unsubscribed: "warning",
  bounced: "muted",
} as const;

export function ContactsTable() {
  return (
    <DataTable
      caption="Static placeholder data until contact APIs are wired"
      columns={[
        { key: "email", label: "Contact" },
        { key: "lifecycle", label: "Lifecycle" },
        { key: "source", label: "Source" },
        { key: "updatedAt", label: "Updated", className: "text-right" },
      ]}
      rows={contacts.map((contact) => ({
        email: (
          <Link
            href={`/contacts/${contact.id}`}
            className="font-medium hover:underline"
          >
            {maskEmailAddress(contact.email)}
          </Link>
        ),
        lifecycle: (
          <Badge variant={lifecycleVariant[contact.lifecycle]}>
            {contact.lifecycle}
          </Badge>
        ),
        source: contact.source,
        updatedAt: formatTimestamp(contact.updatedAt),
      }))}
    />
  );
}
