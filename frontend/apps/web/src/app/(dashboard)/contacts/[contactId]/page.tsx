import { getContactById } from "../_lib/contacts-queries";
import { ContactDrawer } from "../_components/contact-drawer";

type ContactDetailPageProps = {
  params: Promise<{ contactId: string }>;
};

export default async function ContactDetailPage({
  params,
}: ContactDetailPageProps) {
  const { contactId } = await params;
  const contact = getContactById(contactId);

  return (
    <div className="page-stack">
      <header className="page-header">
        <div>
          <h1 className="page-title">Contact detail</h1>
          <p className="page-description">
            Detail presentation is scaffolded here until the full drawer and
            lifecycle interactions land in Sprint 04.
          </p>
        </div>
      </header>
      <ContactDrawer contact={contact} />
    </div>
  );
}
