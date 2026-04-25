import { describe, expect, it } from "vitest";
import {
  ApiError,
  ConflictError,
  RateLimitedError,
  parseErrorEnvelope,
  toApiError,
} from "@/lib/api/errors";

describe("api error mapping", () => {
  it("parses stable backend envelopes", () => {
    expect(
      parseErrorEnvelope({
        error: {
          code: "conflict",
          message: "Campaign already launched",
          details: {
            campaignId: "cmp-1",
          },
        },
        request_id: "req-123",
      }),
    ).toEqual({
      code: "conflict",
      details: {
        campaignId: "cmp-1",
      },
      message: "Campaign already launched",
      requestId: "req-123",
    });
  });

  it("maps known status codes to typed frontend errors", () => {
    const error = toApiError(
      409,
      {
        error: {
          code: "conflict",
          message: "Campaign already launched",
        },
      },
      {
        method: "POST",
        path: "/campaigns/cmp-1/launch",
      },
    );

    expect(error).toBeInstanceOf(ConflictError);
    expect(error.message).toBe("Campaign already launched");
    expect(error.path).toBe("/campaigns/cmp-1/launch");
    expect(error.method).toBe("POST");
  });

  it("keeps retry-after metadata on rate-limited errors", () => {
    const error = toApiError(
      429,
      {
        message: "Slow down",
      },
      {
        method: "GET",
        path: "/analytics/overview",
        retryAfterSeconds: 30,
      },
    );

    expect(error).toBeInstanceOf(RateLimitedError);
    expect(error.retryAfterSeconds).toBe(30);
  });

  it("falls back to a generic ApiError when the payload is not structured", () => {
    const error = toApiError(500, "Server exploded", {
      method: "GET",
      path: "/domains",
    });

    expect(error).toBeInstanceOf(ApiError);
    expect(error.message).toContain("/domains");
  });
});
