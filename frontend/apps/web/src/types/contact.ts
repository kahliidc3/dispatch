export type ContactLifecycle =
  | "active"
  | "suppressed"
  | "unsubscribed"
  | "bounced";

export type ContactRecord = {
  id: string;
  email: string;
  lifecycle: ContactLifecycle;
  source: string;
  updatedAt: string;
};
