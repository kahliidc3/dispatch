import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-[6px] px-2.5 py-0.5 text-xs font-medium",
  {
    variants: {
      variant: {
        default: "bg-surface-muted text-foreground",
        outline: "border border-border-strong bg-surface text-foreground",
        success: "bg-[color:var(--success-bg)] text-[color:var(--accent)]",
        warning: "bg-[color:var(--warning-bg)] text-[color:var(--secondary)]",
        danger: "bg-[color:var(--danger-bg)] text-[color:var(--danger)]",
        muted: "bg-[color:var(--neutral-bg)] text-[color:var(--text-muted)]",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  },
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

export function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  );
}
