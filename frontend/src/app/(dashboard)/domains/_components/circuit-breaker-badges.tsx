import { Badge } from "@/components/ui/badge";
import type { BreakerState } from "@/types/domain";

type CircuitBreakerBadgesProps = {
  state: BreakerState;
};

export function CircuitBreakerBadges({
  state,
}: CircuitBreakerBadgesProps) {
  return (
    <Badge variant={state === "open" ? "danger" : "success"}>{state}</Badge>
  );
}
