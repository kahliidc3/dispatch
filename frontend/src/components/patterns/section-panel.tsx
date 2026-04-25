import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

type SectionPanelProps = {
  title?: string;
  description?: string;
  actions?: ReactNode;
  children: ReactNode;
  className?: string;
  contentClassName?: string;
};

export function SectionPanel({
  title,
  description,
  actions,
  children,
  className,
  contentClassName,
}: SectionPanelProps) {
  return (
    <section className={cn("surface-panel section-panel", className)}>
      {title || description || actions ? (
        <div className="panel-header">
          <div className="panel-copy">
            {title ? <h2 className="panel-title">{title}</h2> : null}
            {description ? (
              <p className="panel-description">{description}</p>
            ) : null}
          </div>
          {actions ? <div className="page-actions">{actions}</div> : null}
        </div>
      ) : null}
      <div className={cn("section-stack", contentClassName)}>{children}</div>
    </section>
  );
}
