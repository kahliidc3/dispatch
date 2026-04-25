export type ContactLifecycle =
  | "active"
  | "bounced"
  | "complained"
  | "unsubscribed"
  | "suppressed"
  | "deleted";

export type ContactSource = "csv_import" | "api" | "manual" | "webhook";

export type ContactListMembership = {
  listId: string;
  listName: string;
  addedAt: string;
};

export type ContactPreference = {
  key: string;
  label: string;
  subscribed: boolean;
};

export type ContactEventType =
  | "sent"
  | "delivered"
  | "bounced"
  | "complained"
  | "opened"
  | "clicked"
  | "unsubscribed";

export type ContactEvent = {
  id: string;
  type: ContactEventType;
  occurredAt: string;
  detail: string | null;
};

export type ContactListItem = {
  id: string;
  email: string;
  firstName: string | null;
  lastName: string | null;
  lifecycle: ContactLifecycle;
  source: ContactSource;
  createdAt: string;
  updatedAt: string;
};

export type ContactDetail = ContactListItem & {
  suppressedAt: string | null;
  suppressionReason: string | null;
  lists: ContactListMembership[];
  preferences: ContactPreference[];
  recentEvents: ContactEvent[];
};
