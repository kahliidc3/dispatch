import type { ApiError } from "@/lib/api/errors";
import { publicEnv } from "@/lib/env";

type Primitive = string | number | boolean | null;
type TelemetryObject = {
  [key: string]: TelemetryValue;
};

type TelemetryArray = TelemetryValue[];

type TelemetryValue = Primitive | TelemetryArray | TelemetryObject;

export type TelemetryEvent = {
  event: string;
  props?: Record<string, TelemetryValue>;
  level?: "info" | "error";
  requestId?: string | null;
};

const emailPattern =
  /\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b/gi;

async function sha256(value: string) {
  const encoded = new TextEncoder().encode(value.trim().toLowerCase());
  const digest = await crypto.subtle.digest("SHA-256", encoded);

  return Array.from(new Uint8Array(digest))
    .map((byte) => byte.toString(16).padStart(2, "0"))
    .join("")
    .slice(0, 16);
}

async function sanitizeString(value: string) {
  const matches = value.match(emailPattern);

  if (!matches) {
    return value;
  }

  let sanitized = value;

  for (const match of matches) {
    const hashed = await sha256(match);
    sanitized = sanitized.replaceAll(match, `[email:${hashed}]`);
  }

  return sanitized;
}

async function sanitizeValue(value: TelemetryValue): Promise<TelemetryValue> {
  if (typeof value === "string") {
    return sanitizeString(value);
  }

  if (Array.isArray(value)) {
    return Promise.all(value.map((entry) => sanitizeValue(entry)));
  }

  if (typeof value === "number" || typeof value === "boolean" || value === null) {
    return value;
  }

  return Object.fromEntries(
    await Promise.all(
      Object.entries(value).map(async ([key, entry]) => [key, await sanitizeValue(entry)]),
    ),
  );
}

export async function sanitizeTelemetryEvent(event: TelemetryEvent) {
  return {
    ...event,
    props: event.props ? ((await sanitizeValue(event.props)) as TelemetryEvent["props"]) : undefined,
  } satisfies TelemetryEvent;
}

function normalizeTelemetryEvent(
  eventOrName: string | TelemetryEvent,
  props?: TelemetryEvent["props"],
) {
  if (typeof eventOrName === "string") {
    return {
      event: eventOrName,
      props,
      level: "info",
    } satisfies TelemetryEvent;
  }

  return eventOrName;
}

export async function track(
  eventOrName: string | TelemetryEvent,
  props?: TelemetryEvent["props"],
) {
  const telemetryEvent = await sanitizeTelemetryEvent(
    normalizeTelemetryEvent(eventOrName, props),
  );

  if (!publicEnv.NEXT_PUBLIC_TELEMETRY_ENDPOINT) {
    return telemetryEvent;
  }

  const payload = JSON.stringify(telemetryEvent);

  if (typeof navigator !== "undefined" && "sendBeacon" in navigator) {
    navigator.sendBeacon(
      publicEnv.NEXT_PUBLIC_TELEMETRY_ENDPOINT,
      new Blob([payload], { type: "application/json" }),
    );
    return telemetryEvent;
  }

  await fetch(publicEnv.NEXT_PUBLIC_TELEMETRY_ENDPOINT, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: payload,
    keepalive: true,
  });

  return telemetryEvent;
}

export async function trackError(
  error: Error | ApiError | unknown,
  context?: Record<string, TelemetryValue>,
) {
  const resolvedError = error instanceof Error ? error : new Error("Unknown error");

  return track({
    event: "frontend.error",
    level: "error",
    props: {
      ...context,
      errorName: resolvedError.name,
      errorMessage: resolvedError.message,
      digest:
        typeof error === "object" &&
        error !== null &&
        "digest" in error &&
        typeof error.digest === "string"
          ? error.digest
          : null,
    },
  });
}
