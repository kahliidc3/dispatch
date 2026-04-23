import type { ReactElement, ReactNode } from "react";
import { Children, isValidElement } from "react";
import { describe, expect, it } from "vitest";
import RootLayout, { metadata } from "@/app/layout";
import { Toaster } from "@/components/ui/sonner";

describe("RootLayout", () => {
  it("wraps the app in the root html and body shell", () => {
    const tree = RootLayout({
      children: <div data-testid="child">Child</div>,
    });

    expect(isValidElement(tree)).toBe(true);
    if (!isValidElement(tree)) {
      return;
    }

    const html = tree as ReactElement<{ children: ReactNode; lang: string }>;

    expect(html.type).toBe("html");
    expect(html.props.lang).toBe("en");

    const body = html.props.children;
    expect(isValidElement(body)).toBe(true);
    if (!isValidElement(body)) {
      return;
    }

    const bodyElement = body as ReactElement<{ children: ReactNode }>;

    expect(bodyElement.type).toBe("body");

    const bodyChildren = Children.toArray(bodyElement.props.children);
    expect(bodyChildren).toHaveLength(2);

    expect(isValidElement(bodyChildren[0])).toBe(true);
    if (isValidElement(bodyChildren[0])) {
      const child = bodyChildren[0] as ReactElement<{ "data-testid": string }>;
      expect(child.props["data-testid"]).toBe("child");
    }

    expect(isValidElement(bodyChildren[1])).toBe(true);
    if (isValidElement(bodyChildren[1])) {
      expect(bodyChildren[1].type).toBe(Toaster);
    }
  });

  it("exports the root metadata contract", () => {
    expect(metadata.description).toBe(
      "Frontend bootstrap for the Dispatch operator console.",
    );
    expect(metadata.title).toMatchObject({
      default: "Dispatch",
      template: "%s | Dispatch",
    });
  });
});
