import { describe, expect, it } from "vitest";
import { sanitizeTelemetryEvent, trackError } from "@/lib/telemetry";

describe("telemetry", () => {
  it("redacts email addresses before returning telemetry payloads", async () => {
    const payload = await sanitizeTelemetryEvent({
      event: "frontend.error",
      props: {
        contact: "ops@dispatch.internal",
        nested: {
          owner: "owner@dispatch.internal",
        },
      },
    });

    expect(payload.props?.contact).toMatch(/^\[email:/);
    expect(payload.props?.nested).toMatchObject({
      owner: expect.stringMatching(/^\[email:/),
    });
  });

  it("normalizes frontend errors without throwing", async () => {
    const payload = await trackError(new Error("fatal"));

    expect(payload.event).toBe("frontend.error");
    expect(payload.props).toMatchObject({
      errorMessage: "fatal",
      errorName: "Error",
    });
  });
});
