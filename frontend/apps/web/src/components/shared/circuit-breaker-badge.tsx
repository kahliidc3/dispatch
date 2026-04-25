import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import type { BreakerEntryState, BreakerScope } from "@/types/ops";

type CircuitBreakerBadgeProps = {
  scope: BreakerScope;
  entityId: string;
  state: BreakerEntryState;
};

const stateVariant: Record<
  BreakerEntryState,
  "danger" | "warning" | "success"
> = {
  open: "danger",
  half_open: "warning",
  closed: "success",
};

export function CircuitBreakerBadge({
  scope,
  entityId,
  state,
}: CircuitBreakerBadgeProps) {
  return (
    <Link
      href={`/ops/circuit-breakers?scope=${scope}&entity=${entityId}`}
      aria-label={`Circuit breaker ${state} — view in console`}
    >
      <Badge variant={stateVariant[state]}>{state}</Badge>
    </Link>
  );
}
