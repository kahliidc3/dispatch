import Link from "next/link";
import { notFound } from "next/navigation";
import { SegmentWorkspace } from "../_components/segment-workspace";
import { getSegmentById } from "../_lib/segments-queries";

type SegmentDetailPageProps = {
  params: Promise<{ segmentId: string }>;
};

export default async function SegmentDetailPage({
  params,
}: SegmentDetailPageProps) {
  const { segmentId } = await params;

  const segment = getSegmentById(segmentId);
  if (!segment) notFound();

  return (
    <div className="page-stack">
      <nav
        className="flex items-center gap-2 text-sm text-text-muted"
        aria-label="Breadcrumb"
      >
        <Link href="/segments" className="hover:underline">
          Segments
        </Link>
        <span aria-hidden="true">/</span>
        <span>{segment.name}</span>
      </nav>

      <header className="page-intro">
        <div className="page-intro-copy">
          <h1 className="page-title">{segment.name}</h1>
          {segment.description ? (
            <p className="page-description">{segment.description}</p>
          ) : null}
        </div>
      </header>

      <SegmentWorkspace segment={segment} />
    </div>
  );
}
