import Link from "next/link";
import { notFound } from "next/navigation";
import { PageIntro } from "@/components/patterns/page-intro";
import { isAdmin } from "@/lib/auth/guards";
import { getSession } from "@/lib/auth/session";
import { getContactDetail } from "../_lib/contacts-queries";
import { ContactDrawer } from "../_components/contact-drawer";
import { DeleteContactButton } from "../_components/delete-contact-button";

type ContactDetailPageProps = {
  params: Promise<{ contactId: string }>;
};

export default async function ContactDetailPage({
  params,
}: ContactDetailPageProps) {
  const { contactId } = await params;
  const contact = getContactDetail(contactId);

  if (!contact) notFound();

  const session = await getSession();
  const adminUser = isAdmin(session);

  return (
    <div className="page-stack">
      <nav className="flex items-center gap-2 text-sm text-text-muted" aria-label="Breadcrumb">
        <Link href="/contacts" className="hover:underline">
          Contacts
        </Link>
        <span aria-hidden="true">/</span>
        <span>{contact.email}</span>
      </nav>
      <PageIntro
        title={contact.email}
        description={`Contact ID: ${contact.id}`}
        actions={
          adminUser ? (
            <DeleteContactButton
              contactId={contact.id}
              email={contact.email}
            />
          ) : undefined
        }
      />
      <ContactDrawer contact={contact} />
    </div>
  );
}
