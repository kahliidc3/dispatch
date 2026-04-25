import { PageIntro } from "@/components/patterns/page-intro";
import { lists } from "./_lib/lists-queries";
import { ListsManager } from "./_components/lists-manager";

export default function ListsPage() {
  return (
    <div className="page-stack">
      <PageIntro
        title="Lists"
        description="Organize contacts into named lists and use them to target campaign sends."
      />
      <ListsManager initialLists={lists} />
    </div>
  );
}
