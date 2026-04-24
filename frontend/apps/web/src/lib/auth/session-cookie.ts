import "server-only";
import { createHmac, timingSafeEqual } from "node:crypto";
import { cookies } from "next/headers";
import { z } from "zod";
import { getServerEnv } from "@/lib/env";
import { maskEmailAddress } from "@/lib/formatters";
import { sanitizeNextUrl } from "@/lib/auth/redirects";
import { toTitleCase } from "@/lib/utils";
import type {
  AuthChallengeSummary,
  SessionSource,
  SessionUser,
} from "@/types/api";

const sessionCookieSchema = z.object({
  id: z.string().trim().min(1),
  email: z.string().trim().email(),
  name: z.string().trim().min(1),
  role: z.enum(["admin", "user"]),
  source: z.enum(["backend", "dev"]),
  issuedAt: z.string().datetime(),
});

const authChallengeCookieSchema = z.object({
  id: z.string().trim().min(1),
  email: z.string().trim().email(),
  code: z.string().trim().regex(/^\d{6}$/),
  nextUrl: z.string().trim().min(1),
  attemptsRemaining: z.number().int().nonnegative(),
  expiresAt: z.string().datetime(),
});

type SessionCookiePayload = z.infer<typeof sessionCookieSchema>;
type AuthChallengeCookiePayload = z.infer<typeof authChallengeCookieSchema>;

export type ResolvedSession = {
  session: SessionUser;
  source: SessionSource;
};

export type ResolvedAuthChallenge = {
  challenge: AuthChallengeCookiePayload;
  summary: AuthChallengeSummary;
};

function sign(value: string, secret: string) {
  return createHmac("sha256", secret).update(value).digest("base64url");
}

function toBuffer(value: string) {
  return Buffer.from(value, "utf8");
}

function encodeSignedPayload(payload: object) {
  const { DISPATCH_WEB_SESSION_SECRET } = getServerEnv();
  const encodedPayload = Buffer.from(JSON.stringify(payload), "utf8").toString(
    "base64url",
  );

  return `${encodedPayload}.${sign(encodedPayload, DISPATCH_WEB_SESSION_SECRET)}`;
}

function decodeSignedPayload<T>(
  value: string | undefined,
  schema: z.ZodType<T>,
) {
  if (!value) {
    return null;
  }

  const [encodedPayload, encodedSignature] = value.split(".");

  if (!encodedPayload || !encodedSignature) {
    return null;
  }

  const { DISPATCH_WEB_SESSION_SECRET } = getServerEnv();
  const expectedSignature = sign(encodedPayload, DISPATCH_WEB_SESSION_SECRET);

  if (expectedSignature.length !== encodedSignature.length) {
    return null;
  }

  if (
    !timingSafeEqual(toBuffer(expectedSignature), toBuffer(encodedSignature))
  ) {
    return null;
  }

  try {
    const decodedPayload = Buffer.from(encodedPayload, "base64url").toString(
      "utf8",
    );
    return schema.parse(JSON.parse(decodedPayload));
  } catch {
    return null;
  }
}

export function createSignedSessionValue(
  session: SessionUser,
  source: SessionSource,
) {
  const payload: SessionCookiePayload = {
    ...session,
    source,
    issuedAt: new Date().toISOString(),
  };

  return encodeSignedPayload(payload);
}

export function parseSignedSessionValue(value: string | undefined) {
  const parsed = decodeSignedPayload(value, sessionCookieSchema);

  if (!parsed) {
    return null;
  }

  return {
    session: {
      id: parsed.id,
      email: parsed.email,
      name: parsed.name,
      role: parsed.role,
    },
    source: parsed.source,
  } satisfies ResolvedSession;
}

export function createDevSessionUser(email?: string) {
  const serverEnv = getServerEnv();
  const resolvedEmail = email?.trim() || serverEnv.DISPATCH_DEV_SESSION_EMAIL;
  const localPart = resolvedEmail.split("@")[0] ?? "";
  const derivedName =
    localPart.length > 0
      ? toTitleCase(localPart.replace(/[._-]+/g, " "))
      : serverEnv.DISPATCH_DEV_SESSION_NAME;

  return {
    id: `dev:${resolvedEmail.toLowerCase()}`,
    email: resolvedEmail.toLowerCase(),
    name: derivedName || serverEnv.DISPATCH_DEV_SESSION_NAME,
    role: serverEnv.DISPATCH_DEV_SESSION_ROLE,
  } satisfies SessionUser;
}

export function createSignedAuthChallengeValue(
  challenge: AuthChallengeCookiePayload,
) {
  return encodeSignedPayload(challenge);
}

export function parseSignedAuthChallengeValue(value: string | undefined) {
  const parsed = decodeSignedPayload(value, authChallengeCookieSchema);

  if (!parsed) {
    return null;
  }

  return {
    challenge: parsed,
    summary: {
      maskedEmail: maskEmailAddress(parsed.email),
      expiresAt: parsed.expiresAt,
      nextUrl: sanitizeNextUrl(parsed.nextUrl),
    },
  } satisfies ResolvedAuthChallenge;
}

export function createDevAuthChallenge(input: {
  email: string;
  nextUrl?: string | null;
}) {
  const serverEnv = getServerEnv();

  return {
    id: crypto.randomUUID(),
    email: input.email.trim().toLowerCase(),
    code: serverEnv.DISPATCH_DEV_MFA_CODE,
    nextUrl: sanitizeNextUrl(input.nextUrl),
    attemptsRemaining: serverEnv.DISPATCH_WEB_MFA_MAX_ATTEMPTS,
    expiresAt: new Date(
      Date.now() + serverEnv.DISPATCH_WEB_MFA_CHALLENGE_MAX_AGE_SECONDS * 1000,
    ).toISOString(),
  } satisfies AuthChallengeCookiePayload;
}

export async function readCookieSession() {
  const cookieStore = await cookies();
  const { DISPATCH_WEB_SESSION_COOKIE_NAME } = getServerEnv();

  return parseSignedSessionValue(
    cookieStore.get(DISPATCH_WEB_SESSION_COOKIE_NAME)?.value,
  );
}

export async function readAuthChallenge() {
  const cookieStore = await cookies();
  const { DISPATCH_WEB_CHALLENGE_COOKIE_NAME } = getServerEnv();

  return parseSignedAuthChallengeValue(
    cookieStore.get(DISPATCH_WEB_CHALLENGE_COOKIE_NAME)?.value,
  );
}

export function isAuthChallengeExpired(expiresAt: string) {
  return new Date(expiresAt).getTime() <= Date.now();
}

export function getSessionCookieOptions() {
  const serverEnv = getServerEnv();

  return {
    httpOnly: true,
    maxAge: serverEnv.DISPATCH_WEB_SESSION_MAX_AGE_SECONDS,
    path: "/",
    sameSite: "strict" as const,
    secure: serverEnv.NODE_ENV === "production",
  };
}

export function getChallengeCookieOptions() {
  const serverEnv = getServerEnv();

  return {
    httpOnly: true,
    maxAge: serverEnv.DISPATCH_WEB_MFA_CHALLENGE_MAX_AGE_SECONDS,
    path: "/",
    sameSite: "strict" as const,
    secure: serverEnv.NODE_ENV === "production",
  };
}
