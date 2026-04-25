import { NextResponse } from "next/server";
import { z } from "zod";
import { getServerEnv } from "@/lib/env";
import {
  clearLoginFailures,
  getLoginLockout,
  registerLoginFailure,
} from "@/lib/auth/dev-session-store";
import { getResolvedSession } from "@/lib/auth/session";
import { maskEmailAddress } from "@/lib/formatters";
import {
  createDevAuthChallenge,
  createDevSessionUser,
  createSignedAuthChallengeValue,
  createSignedSessionValue,
  getChallengeCookieOptions,
  getSessionCookieOptions,
  isAuthChallengeExpired,
  readAuthChallenge,
} from "@/lib/auth/session-cookie";
import type { SessionResponse } from "@/types/api";

const loginBodySchema = z.object({
  email: z.string().trim().email(),
  password: z.string().trim().min(8),
  nextUrl: z.string().trim().optional(),
});

const verifyMfaBodySchema = z.object({
  code: z.string().trim().regex(/^\d{6}$/),
  nextUrl: z.string().trim().optional(),
});

export async function GET() {
  const response = NextResponse.json(await getResolvedSession());
  const challenge = await readAuthChallenge();

  if (challenge && isAuthChallengeExpired(challenge.challenge.expiresAt)) {
    clearChallengeCookie(response);
  }

  return response;
}

function createErrorResponse(
  status: number,
  code: string,
  message: string,
  retryAfterSeconds?: number | null,
) {
  const response = NextResponse.json(
    {
      error: {
        code,
        message,
      },
    },
    { status },
  );

  if (retryAfterSeconds) {
    response.headers.set("retry-after", String(retryAfterSeconds));
  }

  return response;
}

function clearSessionCookie(response: NextResponse) {
  const { DISPATCH_WEB_SESSION_COOKIE_NAME } = getServerEnv();

  response.cookies.set(DISPATCH_WEB_SESSION_COOKIE_NAME, "", {
    ...getSessionCookieOptions(),
    maxAge: 0,
  });
}

function clearChallengeCookie(response: NextResponse) {
  const { DISPATCH_WEB_CHALLENGE_COOKIE_NAME } = getServerEnv();

  response.cookies.set(DISPATCH_WEB_CHALLENGE_COOKIE_NAME, "", {
    ...getChallengeCookieOptions(),
    maxAge: 0,
  });
}

function isAllowedOrigin(request: Request) {
  const origin = request.headers.get("origin");

  if (!origin) {
    return true;
  }

  const configuredOrigin = getServerEnv().DISPATCH_WEB_APP_ORIGIN;
  const requestOrigin = new URL(request.url).origin;

  return origin === requestOrigin || origin === configuredOrigin;
}

export async function POST(request: Request) {
  const serverEnv = getServerEnv();

  if (!serverEnv.DISPATCH_WEB_ENABLE_DEV_SESSION) {
    return NextResponse.json(
      {
        error: {
          code: "forbidden",
          message:
            "Session creation is disabled until backend authentication is wired.",
        },
      },
      { status: 403 },
    );
  }

  if (!isAllowedOrigin(request)) {
    return createErrorResponse(403, "forbidden", "Cross-site sign-in is not allowed.");
  }

  const rawBody = await request
    .json()
    .catch(() => ({}));
  const payload = loginBodySchema.safeParse(rawBody);

  if (!payload.success) {
    return createErrorResponse(400, "validation_error", "Email and password are required.");
  }

  const normalizedEmail = payload.data.email.trim().toLowerCase();
  const retryAfterSeconds = getLoginLockout(normalizedEmail);

  if (retryAfterSeconds) {
    return createErrorResponse(
      429,
      "rate_limited",
      "Sign-in unavailable - try again later.",
      retryAfterSeconds,
    );
  }

  if (payload.data.password !== serverEnv.DISPATCH_DEV_PASSWORD) {
    const failureState = registerLoginFailure(normalizedEmail);

    return failureState.locked
      ? createErrorResponse(
          429,
          "rate_limited",
          "Sign-in unavailable - try again later.",
          failureState.retryAfterSeconds,
        )
      : createErrorResponse(
          401,
          "invalid_credentials",
          "Check your email or password and try again.",
        );
  }

  clearLoginFailures(normalizedEmail);
  const challenge = createDevAuthChallenge({
    email: normalizedEmail,
    nextUrl: payload.data.nextUrl,
  });
  const responsePayload: SessionResponse = {
    status: "mfa_required",
    session: null,
    source: null,
    challenge: {
      maskedEmail: maskEmailAddress(challenge.email),
      expiresAt: challenge.expiresAt,
      nextUrl: challenge.nextUrl,
    },
    nextUrl: challenge.nextUrl,
  };
  const response = NextResponse.json(responsePayload);

  clearSessionCookie(response);
  response.cookies.set(
    serverEnv.DISPATCH_WEB_CHALLENGE_COOKIE_NAME,
    createSignedAuthChallengeValue(challenge),
    getChallengeCookieOptions(),
  );

  return response;
}

export async function PUT(request: Request) {
  const serverEnv = getServerEnv();

  if (!serverEnv.DISPATCH_WEB_ENABLE_DEV_SESSION) {
    return createErrorResponse(
      403,
      "forbidden",
      "MFA verification is disabled until backend authentication is wired.",
    );
  }

  if (!isAllowedOrigin(request)) {
    return createErrorResponse(
      403,
      "forbidden",
      "Cross-site verification is not allowed.",
    );
  }

  const rawBody = await request
    .json()
    .catch(() => ({}));
  const payload = verifyMfaBodySchema.safeParse(rawBody);

  if (!payload.success) {
    return createErrorResponse(400, "validation_error", "A six-digit code is required.");
  }

  const currentChallenge = await readAuthChallenge();

  if (!currentChallenge || isAuthChallengeExpired(currentChallenge.challenge.expiresAt)) {
    const response = createErrorResponse(
      401,
      "challenge_expired",
      "The verification challenge expired. Start again.",
    );

    clearChallengeCookie(response);
    clearSessionCookie(response);
    return response;
  }

  if (payload.data.code !== currentChallenge.challenge.code) {
    const attemptsRemaining = currentChallenge.challenge.attemptsRemaining - 1;

    if (attemptsRemaining <= 0) {
      const response = createErrorResponse(
        429,
        "rate_limited",
        "Verification unavailable - start again.",
        serverEnv.DISPATCH_WEB_MFA_CHALLENGE_MAX_AGE_SECONDS,
      );

      clearChallengeCookie(response);
      clearSessionCookie(response);
      return response;
    }

    const response = createErrorResponse(
      401,
      "invalid_credentials",
      "Code not accepted. Try a fresh code from your authenticator app.",
    );

    response.cookies.set(
      serverEnv.DISPATCH_WEB_CHALLENGE_COOKIE_NAME,
      createSignedAuthChallengeValue({
        ...currentChallenge.challenge,
        attemptsRemaining,
      }),
      getChallengeCookieOptions(),
    );

    return response;
  }

  const session = createDevSessionUser(currentChallenge.challenge.email);
  const nextUrl = currentChallenge.summary.nextUrl ?? payload.data.nextUrl ?? "/";
  const responsePayload: SessionResponse = {
    status: "authenticated",
    session,
    source: "dev",
    challenge: null,
    nextUrl,
  };
  const response = NextResponse.json(responsePayload);

  response.cookies.set(
    serverEnv.DISPATCH_WEB_SESSION_COOKIE_NAME,
    createSignedSessionValue(session, "dev"),
    getSessionCookieOptions(),
  );
  clearChallengeCookie(response);

  return response;
}

export async function DELETE(request: Request) {
  if (!isAllowedOrigin(request)) {
    return createErrorResponse(403, "forbidden", "Cross-site sign-out is not allowed.");
  }

  const response = NextResponse.json({
    status: "anonymous",
    session: null,
    source: null,
    challenge: null,
    nextUrl: null,
  } satisfies SessionResponse);

  clearSessionCookie(response);
  clearChallengeCookie(response);

  return response;
}
