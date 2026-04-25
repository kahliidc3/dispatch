import "server-only";
import { redirect } from "next/navigation";
import type { SessionResponse } from "@/types/api";
import { sanitizeNextUrl } from "./redirects";
import { requireSession } from "./session";

export function isAdmin(session: SessionResponse["session"]) {
  return session?.role === "admin";
}

export function isSignedIn(session: SessionResponse["session"]) {
  return session !== null;
}

export async function requireUser() {
  return requireSession();
}

export async function requireAdmin() {
  const session = await requireSession();

  if (!isAdmin(session)) {
    redirect(sanitizeNextUrl("/"));
  }

  return session;
}
