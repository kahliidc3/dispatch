import Link from "next/link";
import { Button } from "@/components/ui/button";
import { PageIntro } from "@/components/patterns/page-intro";
import { contactList } from "./_lib/contacts-queries";
import { lists } from "../lists/_lib/lists-queries";
import { ContactsTable } from "./_components/contacts-table";

export default function ContactsPage() {
  return (
    <div className="page-stack">
      <PageIntro
        title="Contacts"
        description="Browse, filter, and manage contacts. Select rows to bulk unsubscribe or update list membership."
        actions={
          <div className="flex gap-3">
            <Button asChild variant="outline">
              <Link href="/contacts/import">Import CSV</Link>
            </Button>
            <Button asChild>
              <Link href="/contacts/new">Add contact</Link>
            </Button>
          </div>
        }
      />
      <ContactsTable contacts={contactList} lists={lists} />
    </div>
  );
}
