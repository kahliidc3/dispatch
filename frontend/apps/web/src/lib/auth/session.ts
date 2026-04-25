import "server-only";
import { cache } from "react";
import { headers } from "next/headers";
import { redirect } from "next/navigation";
import type { SessionResponse } from "@/types/api";
import { buildLoginUrl } from "./redirects";
import {
  isAuthChallengeExpired,
  readAuthChallenge,
  readCookieSession,
} from "./session-cookie";

export const getSession = cache(
  async (): Promise<SessionResponse["session"]> => (await readCookieSession())?.session ?? null,
);

export const getResolvedSession = cache(
  async (): Promise<SessionResponse> => {
    const resolved = await readCookieSession();
    const currentChallenge = await readAuthChallenge();
    const challenge =
      currentChallenge && !isAuthChallengeExpired(currentChallenge.challenge.expiresAt)
        ? currentChallenge.summary
        : null;

    return {
      status: resolved ? "authenticated" : challenge ? "mfa_required" : "anonymous",
      session: resolved?.session ?? null,
      source: resolved?.source ?? null,
      challenge,
      nextUrl: challenge?.nextUrl ?? null,
    };
  },
);

export async function requireSession() {
  const session = await getSession();

  if (!session) {
    const headerStore = await headers();
    redirect(buildLoginUrl(headerStore.get("x-dispatch-next-url")));
  }

  return session;
}
