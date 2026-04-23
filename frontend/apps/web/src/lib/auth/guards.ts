import type { SessionResponse } from "@/types/api";

export function isAdmin(session: SessionResponse["session"]) {
  return session?.role === "admin";
}

export function isSignedIn(session: SessionResponse["session"]) {
  return session !== null;
}
