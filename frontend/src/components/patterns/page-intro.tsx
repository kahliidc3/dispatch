import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

type PageIntroProps = {
  title: string;
  description: string;
  actions?: ReactNode;
  className?: string;
};

export function PageIntro({
  title,
  description,
  actions,
  className,
}: PageIntroProps) {
  return (
    <header className={cn("page-intro", className)}>
      <div className="page-intro-copy">
        <h1 className="page-title">{title}</h1>
        <p className="page-description">{description}</p>
      </div>
      {actions ? <div className="page-actions">{actions}</div> : null}
    </header>
  );
}
