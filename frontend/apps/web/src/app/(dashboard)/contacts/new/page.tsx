"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { SectionPanel } from "@/components/patterns/section-panel";
import { clientJson } from "@/lib/api/client";
import { apiEndpoints } from "@/lib/api/endpoints";
import type { ContactDetail } from "@/types/contact";

export default function NewContactPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isPending, setIsPending] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const trimmedEmail = email.trim();
    if (!trimmedEmail) {
      setError("Email address is required.");
      return;
    }
    setError(null);
    setIsPending(true);
    try {
      const contact = await clientJson<ContactDetail>(
        apiEndpoints.contacts.create,
        {
          method: "POST",
          body: {
            email: trimmedEmail,
            firstName: firstName.trim() || null,
            lastName: lastName.trim() || null,
          },
        },
      );
      toast.success("Contact created.");
      router.push(`/contacts/${contact.id}`);
    } catch {
      setError("Could not create contact. Check the email address and try again.");
    } finally {
      setIsPending(false);
    }
  }

  return (
    <div className="page-stack">
      <nav className="flex items-center gap-2 text-sm text-text-muted" aria-label="Breadcrumb">
        <Link href="/contacts" className="hover:underline">
          Contacts
        </Link>
        <span aria-hidden="true">/</span>
        <span>New contact</span>
      </nav>
      <header className="page-intro">
        <div className="page-intro-copy">
          <h1 className="page-title">Add contact</h1>
          <p className="page-description">
            Add a single contact manually. For bulk additions use CSV import.
          </p>
        </div>
      </header>
      <SectionPanel title="Contact details">
        <form
          onSubmit={(e) => void handleSubmit(e)}
          className="grid max-w-md gap-4"
        >
          <div>
            <label className="label" htmlFor="new-contact-email">
              Email address *
            </label>
            <Input
              id="new-contact-email"
              type="email"
              required
              placeholder="person@example.com"
              value={email}
              onChange={(e) => {
                setEmail(e.target.value);
                setError(null);
              }}
            />
          </div>
          <div>
            <label className="label" htmlFor="new-contact-first-name">
              First name
            </label>
            <Input
              id="new-contact-first-name"
              type="text"
              placeholder="Optional"
              value={firstName}
              onChange={(e) => setFirstName(e.target.value)}
            />
          </div>
          <div>
            <label className="label" htmlFor="new-contact-last-name">
              Last name
            </label>
            <Input
              id="new-contact-last-name"
              type="text"
              placeholder="Optional"
              value={lastName}
              onChange={(e) => setLastName(e.target.value)}
            />
          </div>
          {error ? <p className="text-sm text-danger">{error}</p> : null}
          <div className="flex gap-3">
            <Button type="submit" disabled={isPending}>
              {isPending ? "Creating…" : "Create contact"}
            </Button>
            <Button type="button" variant="outline" asChild>
              <Link href="/contacts">Cancel</Link>
            </Button>
          </div>
        </form>
      </SectionPanel>
    </div>
  );
}
