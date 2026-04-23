import Link from "next/link";
import { SectionPanel } from "@/components/patterns/section-panel";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

type EmptyStateProps = {
  title: string;
  description: string;
  actionHref?: string;
  actionLabel?: string;
  className?: string;
};

export function EmptyState({
  title,
  description,
  actionHref,
  actionLabel,
  className,
}: EmptyStateProps) {
  return (
    <SectionPanel
      title={title}
      description={description}
      className={cn(className)}
      actions={
        actionHref && actionLabel ? (
          <Button asChild variant="outline">
            <Link href={actionHref}>{actionLabel}</Link>
          </Button>
        ) : null
      }
    >
      <></>
    </SectionPanel>
  );
}
