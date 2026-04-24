import { z } from "zod";

const runtimeSchema = z.enum(["development", "test", "production"]);

const booleanishSchema = z
  .union([z.boolean(), z.string()])
  .transform((value) => {
    if (typeof value === "boolean") {
      return value;
    }

    const normalized = value.trim().toLowerCase();
    return ["1", "true", "yes", "on"].includes(normalized);
  });

const publicEnvSchema = z.object({
  NEXT_PUBLIC_APP_NAME: z.string().trim().min(1).default("Dispatch"),
  NEXT_PUBLIC_API_BASE_URL: z
    .string()
    .trim()
    .min(1)
    .default("http://localhost:8000"),
  NEXT_PUBLIC_TELEMETRY_ENDPOINT: z
    .string()
    .trim()
    .optional()
    .transform((value) => value || null),
});

const serverEnvSchema = z.object({
  DISPATCH_WEB_APP_ORIGIN: z
    .string()
    .trim()
    .url()
    .default("http://localhost:3000"),
  DISPATCH_WEB_ENABLE_DEV_SESSION: booleanishSchema.optional(),
  DISPATCH_WEB_REQUEST_ID_HEADER: z
    .string()
    .trim()
    .min(1)
    .default("x-request-id"),
  DISPATCH_WEB_SESSION_COOKIE_NAME: z
    .string()
    .trim()
    .min(1)
    .default("dispatch_web_session"),
  DISPATCH_WEB_CHALLENGE_COOKIE_NAME: z
    .string()
    .trim()
    .min(1)
    .default("dispatch_web_mfa_challenge"),
  DISPATCH_WEB_SESSION_MAX_AGE_SECONDS: z.coerce
    .number()
    .int()
    .positive()
    .default(60 * 60 * 8),
  DISPATCH_WEB_MFA_CHALLENGE_MAX_AGE_SECONDS: z.coerce
    .number()
    .int()
    .positive()
    .default(60 * 5),
  DISPATCH_WEB_MFA_MAX_ATTEMPTS: z.coerce
    .number()
    .int()
    .positive()
    .default(3),
  DISPATCH_WEB_SESSION_SECRET: z
    .string()
    .trim()
    .min(16)
    .default("dispatch-web-local-session-secret"),
  DISPATCH_DEV_SESSION_EMAIL: z
    .string()
    .trim()
    .email()
    .default("operator@dispatch.internal"),
  DISPATCH_DEV_SESSION_NAME: z
    .string()
    .trim()
    .min(1)
    .default("Dispatch Operator"),
  DISPATCH_DEV_SESSION_ROLE: z.enum(["admin", "user"]).default("admin"),
  DISPATCH_DEV_PASSWORD: z
    .string()
    .trim()
    .min(8)
    .default("dispatch-demo-password"),
  DISPATCH_DEV_MFA_CODE: z
    .string()
    .trim()
    .regex(/^\d{6}$/)
    .default("246810"),
});

export type PublicEnv = z.infer<typeof publicEnvSchema>;
export type ServerEnv = z.infer<typeof serverEnvSchema> & {
  NODE_ENV: z.infer<typeof runtimeSchema>;
  DISPATCH_WEB_ENABLE_DEV_SESSION: boolean;
};

export const publicEnv = publicEnvSchema.parse({
  NEXT_PUBLIC_APP_NAME: process.env.NEXT_PUBLIC_APP_NAME,
  NEXT_PUBLIC_API_BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL,
  NEXT_PUBLIC_TELEMETRY_ENDPOINT: process.env.NEXT_PUBLIC_TELEMETRY_ENDPOINT,
});

export const env = publicEnv;

let serverEnvCache: ServerEnv | null = null;

function readServerRuntimeEnv(name: string) {
  const runtimeEnv = process.env as Record<string, string | undefined>;
  return runtimeEnv[name];
}

export function getServerEnv() {
  if (typeof window !== "undefined") {
    throw new Error("getServerEnv() must only run on the server.");
  }

  if (serverEnvCache) {
    return serverEnvCache;
  }

  const nodeEnv = runtimeSchema.parse(process.env.NODE_ENV ?? "development");
  const parsed = serverEnvSchema.parse({
    DISPATCH_WEB_APP_ORIGIN: readServerRuntimeEnv("DISPATCH_WEB_APP_ORIGIN"),
    DISPATCH_WEB_ENABLE_DEV_SESSION: readServerRuntimeEnv(
      "DISPATCH_WEB_ENABLE_DEV_SESSION",
    ),
    DISPATCH_WEB_REQUEST_ID_HEADER: readServerRuntimeEnv(
      "DISPATCH_WEB_REQUEST_ID_HEADER",
    ),
    DISPATCH_WEB_SESSION_COOKIE_NAME: readServerRuntimeEnv(
      "DISPATCH_WEB_SESSION_COOKIE_NAME",
    ),
    DISPATCH_WEB_CHALLENGE_COOKIE_NAME: readServerRuntimeEnv(
      "DISPATCH_WEB_CHALLENGE_COOKIE_NAME",
    ),
    DISPATCH_WEB_SESSION_MAX_AGE_SECONDS: readServerRuntimeEnv(
      "DISPATCH_WEB_SESSION_MAX_AGE_SECONDS",
    ),
    DISPATCH_WEB_MFA_CHALLENGE_MAX_AGE_SECONDS: readServerRuntimeEnv(
      "DISPATCH_WEB_MFA_CHALLENGE_MAX_AGE_SECONDS",
    ),
    DISPATCH_WEB_MFA_MAX_ATTEMPTS: readServerRuntimeEnv(
      "DISPATCH_WEB_MFA_MAX_ATTEMPTS",
    ),
    DISPATCH_WEB_SESSION_SECRET: readServerRuntimeEnv(
      "DISPATCH_WEB_SESSION_SECRET",
    ),
    DISPATCH_DEV_SESSION_EMAIL: readServerRuntimeEnv("DISPATCH_DEV_SESSION_EMAIL"),
    DISPATCH_DEV_SESSION_NAME: readServerRuntimeEnv("DISPATCH_DEV_SESSION_NAME"),
    DISPATCH_DEV_SESSION_ROLE: readServerRuntimeEnv("DISPATCH_DEV_SESSION_ROLE"),
    DISPATCH_DEV_PASSWORD: readServerRuntimeEnv("DISPATCH_DEV_PASSWORD"),
    DISPATCH_DEV_MFA_CODE: readServerRuntimeEnv("DISPATCH_DEV_MFA_CODE"),
  });

  const serverEnv = {
    ...parsed,
    NODE_ENV: nodeEnv,
    DISPATCH_WEB_ENABLE_DEV_SESSION:
      parsed.DISPATCH_WEB_ENABLE_DEV_SESSION ?? nodeEnv !== "production",
  } satisfies ServerEnv;

  if (
    serverEnv.NODE_ENV === "production" &&
    serverEnv.DISPATCH_WEB_ENABLE_DEV_SESSION &&
    serverEnv.DISPATCH_WEB_SESSION_SECRET ===
      "dispatch-web-local-session-secret"
  ) {
    throw new Error(
      "DISPATCH_WEB_SESSION_SECRET must be overridden when dev sessions are enabled in production.",
    );
  }

  serverEnvCache = serverEnv;
  return serverEnv;
}
