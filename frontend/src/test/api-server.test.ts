import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { serverJson } from "@/lib/api/server";
import {
  setMockCookies,
  setMockHeaders,
} from "@/test/test-utils/next-headers";

describe("serverJson", () => {
  const fetchMock = vi.fn();

  beforeEach(() => {
    vi.stubGlobal("window", undefined);
    vi.stubGlobal("fetch", fetchMock);
    setMockCookies({
      dispatch_web_session: "session=abc123",
    });
    setMockHeaders({
      "x-request-id": "req-test-123",
    });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    fetchMock.mockReset();
  });

  it("forwards cookies, request ids, and JSON payloads from the server", async () => {
    fetchMock.mockResolvedValueOnce(
      new Response(JSON.stringify({ ok: true }), {
        status: 200,
        headers: {
          "content-type": "application/json",
        },
      }),
    );

    const payload = await serverJson<{ ok: boolean }>("/campaigns", {
      method: "POST",
      body: {
        status: "draft",
      },
      query: {
        page: 2,
      },
    });

    expect(payload).toEqual({ ok: true });
    expect(fetchMock).toHaveBeenCalledTimes(1);

    const [url, init] = fetchMock.mock.calls[0] as [URL, RequestInit];
    expect(String(url)).toBe("http://localhost:8000/campaigns?page=2");

    const headers = init.headers as Headers;
    expect(headers.get("accept")).toBe("application/json");
    expect(headers.get("content-type")).toBe("application/json");
    expect(headers.get("cookie")).toBe("dispatch_web_session=session=abc123");
    expect(headers.get("x-request-id")).toBe("req-test-123");
  });
});
