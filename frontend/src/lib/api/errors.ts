import type { ApiErrorEnvelope } from "@/types/api";

export type ApiErrorContext = {
  path: string;
  method: string;
  requestId?: string | null;
  code?: string;
  details?: Record<string, unknown> | null;
  retryAfterSeconds?: number | null;
};

export class ApiError extends Error {
  readonly path: string;
  readonly method: string;
  readonly requestId: string | null;
  readonly code: string | undefined;
  readonly details: Record<string, unknown> | null;
  readonly retryAfterSeconds: number | null;

  constructor(
    message: string,
    public readonly status: number,
    context: ApiErrorContext,
  ) {
    super(message);
    this.name = "ApiError";
    this.path = context.path;
    this.method = context.method;
    this.requestId = context.requestId ?? null;
    this.code = context.code;
    this.details = context.details ?? null;
    this.retryAfterSeconds = context.retryAfterSeconds ?? null;
  }
}

export class UnauthorizedError extends ApiError {
  constructor(message: string, context: ApiErrorContext) {
    super(message, 401, context);
    this.name = "UnauthorizedError";
  }
}

export class ForbiddenError extends ApiError {
  constructor(message: string, context: ApiErrorContext) {
    super(message, 403, context);
    this.name = "ForbiddenError";
  }
}

export class NotFoundError extends ApiError {
  constructor(message: string, context: ApiErrorContext) {
    super(message, 404, context);
    this.name = "NotFoundError";
  }
}

export class ConflictError extends ApiError {
  constructor(message: string, context: ApiErrorContext) {
    super(message, 409, context);
    this.name = "ConflictError";
  }
}

export class RateLimitedError extends ApiError {
  constructor(message: string, context: ApiErrorContext) {
    super(message, 429, context);
    this.name = "RateLimitedError";
  }
}

export type ParsedErrorEnvelope = {
  message: string;
  code?: string;
  details?: Record<string, unknown> | null;
  requestId?: string | null;
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

export function parseErrorEnvelope(payload: unknown): ParsedErrorEnvelope | null {
  if (!isRecord(payload)) {
    return null;
  }

  const requestId =
    typeof payload.requestId === "string"
      ? payload.requestId
      : typeof payload.request_id === "string"
        ? payload.request_id
        : null;

  const nestedError = isRecord(payload.error) ? payload.error : null;
  const message =
    typeof nestedError?.message === "string"
      ? nestedError.message
      : typeof payload.message === "string"
        ? payload.message
        : typeof payload.detail === "string"
          ? payload.detail
          : null;

  const details =
    nestedError && isRecord(nestedError.details) ? nestedError.details : null;

  const code =
    typeof nestedError?.code === "string"
      ? nestedError.code
      : typeof payload.code === "string"
        ? payload.code
        : undefined;

  if (!message) {
    return null;
  }

  return {
    message,
    code,
    details,
    requestId,
  };
}

export function toApiError(
  status: number,
  payload: unknown,
  context: Omit<ApiErrorContext, "code" | "details" | "requestId"> & {
    requestId?: string | null;
    retryAfterSeconds?: number | null;
  },
) {
  const envelope = parseErrorEnvelope(payload);
  const errorContext: ApiErrorContext = {
    ...context,
    requestId: envelope?.requestId ?? context.requestId ?? null,
    code: envelope?.code,
    details: envelope?.details,
    retryAfterSeconds: context.retryAfterSeconds ?? null,
  };
  const message =
    envelope?.message ?? `Request failed with status ${status} for ${context.path}`;

  switch (status) {
    case 401:
      return new UnauthorizedError(message, errorContext);
    case 403:
      return new ForbiddenError(message, errorContext);
    case 404:
      return new NotFoundError(message, errorContext);
    case 409:
      return new ConflictError(message, errorContext);
    case 429:
      return new RateLimitedError(message, errorContext);
    default:
      return new ApiError(message, status, errorContext);
  }
}

export function createErrorEnvelope(error: ApiError): ApiErrorEnvelope {
  return {
    error: {
      code: error.code ?? "unknown_error",
      message: error.message,
      details: error.details,
    },
    requestId: error.requestId,
  };
}
