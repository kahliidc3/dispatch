export type HealthResponse = {
  service: "web";
  status: "ok";
};

export type SessionUser = {
  id: string;
  name: string;
  role: "admin" | "user";
};

export type SessionResponse = {
  session: SessionUser | null;
};
