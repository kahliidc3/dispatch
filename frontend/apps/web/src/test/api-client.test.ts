import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { clientJson } from "@/lib/api/client";
import { UnauthorizedError } from "@/lib/api/errors";

describe("clientJson", () => {
  const fetchMock = vi.fn();
  const locationAssign = vi.fn();
  const originalLocation = window.location;

  beforeEach(() => {
    vi.stubGlobal("fetch", fetchMock);
    Object.defineProperty(window, "location", {
      configurable: true,
      value: {
        ...originalLocation,
        assign: locationAssign,
        origin: "http://localhost:3000",
      },
    });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    Object.defineProperty(window, "location", {
      configurable: true,
      value: originalLocation,
    });
    fetchMock.mockReset();
    locationAssign.mockReset();
  });

  it("serializes JSON requests and prefixes backend URLs", async () => {
    fetchMock.mockResolvedValueOnce(
      new Response(JSON.stringify({ ok: true }), {
        status: 200,
        headers: {
          "content-type": "application/json",
        },
      }),
    );

    const payload = await clientJson<{ ok: boolean }>("/campaigns", {
      method: "POST",
      body: {
        status: "draft",
      },
      query: {
        page: 1,
      },
      redirectOnUnauthorized: false,
    });

    expect(payload).toEqual({ ok: true });
    expect(fetchMock).toHaveBeenCalledTimes(1);

    const [url, init] = fetchMock.mock.calls[0] as [URL, RequestInit];
    expect(String(url)).toBe("http://localhost:8000/campaigns?page=1");
    expect(init.credentials).toBe("include");
    expect(init.body).toBe(JSON.stringify({ status: "draft" }));

    const headers = init.headers as Headers;
    expect(headers.get("accept")).toBe("application/json");
    expect(headers.get("content-type")).toBe("application/json");
    expect(headers.get("x-request-id")).toBeTruthy();
  });

  it("redirects to login on unauthorized requests by default", async () => {
    fetchMock.mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          error: {
            code: "unauthorized",
            message: "Session expired",
          },
        }),
        {
          status: 401,
          headers: {
            "content-type": "application/json",
          },
        },
      ),
    );

    await expect(clientJson("/campaigns")).rejects.toBeInstanceOf(
      UnauthorizedError,
    );
    expect(locationAssign).toHaveBeenCalledWith("/login");
  });
});
