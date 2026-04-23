import type { SessionResponse } from "@/types/api";

export async function getSession(): Promise<SessionResponse["session"]> {
  return null;
}

export async function requireSession() {
  return getSession();
}
