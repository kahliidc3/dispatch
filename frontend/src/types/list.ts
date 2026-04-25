export type List = {
  id: string;
  name: string;
  description: string | null;
  memberCount: number;
  createdAt: string;
  updatedAt: string;
};

export type ListMember = {
  contactId: string;
  email: string;
  addedAt: string;
};
