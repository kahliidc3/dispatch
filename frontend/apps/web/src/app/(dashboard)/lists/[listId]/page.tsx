import Link from "next/link";
import { notFound } from "next/navigation";
import { PageIntro } from "@/components/patterns/page-intro";
import { getListById, getListMembers } from "../_lib/lists-queries";
import { ListMembersPanel } from "./_components/list-members-panel";

type ListDetailPageProps = {
  params: Promise<{ listId: string }>;
};

export default async function ListDetailPage({
  params,
}: ListDetailPageProps) {
  const { listId } = await params;
  const list = getListById(listId);

  if (!list) notFound();

  const members = getListMembers(listId);

  return (
    <div className="page-stack">
      <nav
        className="flex items-center gap-2 text-sm text-text-muted"
        aria-label="Breadcrumb"
      >
        <Link href="/lists" className="hover:underline">
          Lists
        </Link>
        <span aria-hidden="true">/</span>
        <span>{list.name}</span>
      </nav>
      <PageIntro
        title={list.name}
        description={list.description ?? `${members.length} member(s)`}
      />
      <ListMembersPanel
        listId={listId}
        listName={list.name}
        initialMembers={members}
      />
    </div>
  );
}
