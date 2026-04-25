import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-[6px] px-2.5 py-0.5 text-xs font-medium",
  {
    variants: {
      variant: {
        default: "bg-surface-muted text-foreground",
        outline: "border border-border-strong bg-transparent text-[color:var(--text)]",
        success:
          "bg-[color:color-mix(in_srgb,var(--accent)_16%,white)] text-[color:var(--primary)]",
        warning:
          "bg-[color:color-mix(in_srgb,var(--secondary)_14%,white)] text-[color:var(--primary)]",
        danger: "bg-[color:var(--danger-bg)] text-[color:var(--danger)]",
        muted: "bg-[color:var(--neutral-bg)] text-[color:var(--text)]",
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
