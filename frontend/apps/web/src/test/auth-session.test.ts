import { beforeEach, describe, expect, it, vi } from "vitest";
import {
  createDevAuthChallenge,
  createDevSessionUser,
  createSignedAuthChallengeValue,
  createSignedSessionValue,
  parseSignedAuthChallengeValue,
  parseSignedSessionValue,
} from "@/lib/auth/session-cookie";
import {
  resetNavigationMocks,
  redirectMock,
} from "@/test/test-utils/next-navigation";
import { setMockCookies, setMockHeaders } from "@/test/test-utils/next-headers";

describe("auth session helpers", () => {
  beforeEach(() => {
    vi.stubGlobal("window", undefined);
  });

  it("round-trips a signed dev session cookie", () => {
    const session = createDevSessionUser("ops@dispatch.internal");
    const signedValue = createSignedSessionValue(session, "dev");

    expect(parseSignedSessionValue(signedValue)).toEqual({
      session,
      source: "dev",
    });
  });

  it("round-trips an MFA challenge cookie summary", () => {
    const challenge = createDevAuthChallenge({
      email: "ops@dispatch.internal",
      nextUrl: "/settings/api-keys",
    });
    const signedValue = createSignedAuthChallengeValue(challenge);

    expect(parseSignedAuthChallengeValue(signedValue)).toEqual({
      challenge,
      summary: {
        maskedEmail: "op**@dispatch.internal",
        expiresAt: challenge.expiresAt,
        nextUrl: "/settings/api-keys",
      },
    });
  });

  it("rejects a tampered session cookie", () => {
    const session = createDevSessionUser("ops@dispatch.internal");
    const signedValue = createSignedSessionValue(session, "dev");

    expect(parseSignedSessionValue(`${signedValue}tampered`)).toBeNull();
  });

  it("redirects protected routes when no session is present", async () => {
    vi.resetModules();
    resetNavigationMocks();
    setMockCookies({});
    setMockHeaders({
      "x-dispatch-next-url": "/domains?tab=health",
    });

    const { requireSession } = await import("@/lib/auth/session");

    await expect(requireSession()).rejects.toThrow(
      "NEXT_REDIRECT:/login?next=%2Fdomains%3Ftab%3Dhealth",
    );
    expect(redirectMock).toHaveBeenCalledWith(
      "/login?next=%2Fdomains%3Ftab%3Dhealth",
    );
  });
});
