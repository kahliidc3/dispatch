import Link from "next/link";
import { Button } from "@/components/ui/button";
import { ContactsTable } from "./_components/contacts-table";

export default function ContactsPage() {
  return (
    <div className="page-stack">
      <header className="page-header">
        <div>
          <h1 className="page-title">Contacts</h1>
          <p className="page-description">
            Contact browser, drawers, lifecycle controls, and list management
            will be implemented in later sprints. The scaffold locks the route
            and table surface now.
          </p>
        </div>
        <div className="flex gap-3">
          <Button asChild variant="outline">
            <Link href="/contacts/import">Import placeholder</Link>
          </Button>
          <Button asChild>
            <Link href="/contacts/ctc-001">Open sample contact</Link>
          </Button>
        </div>
      </header>
      <ContactsTable />
    </div>
  );
}
