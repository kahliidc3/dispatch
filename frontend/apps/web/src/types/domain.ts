export type DomainVerification = "pending" | "verifying" | "verified";
export type DomainReputation = "warming" | "healthy" | "cooling";
export type BreakerState = "closed" | "open";

export type DomainRecord = {
  id: string;
  name: string;
  verification: DomainVerification;
  reputation: DomainReputation;
  breaker: BreakerState;
  updatedAt: string;
};
