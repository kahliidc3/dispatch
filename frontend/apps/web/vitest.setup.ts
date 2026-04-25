import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import React from "react";
import { afterEach, vi } from "vitest";
import {
  getMockPathname,
  redirectMock,
  resetNavigationMocks,
  routerMock,
} from "@/test/test-utils/next-navigation";
import {
  cookiesMock,
  headersMock,
  resetHeadersMocks,
} from "@/test/test-utils/next-headers";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  resetNavigationMocks();
  resetHeadersMocks();
});

vi.mock("next/link", () => ({
  default: ({
    href,
    children,
    ...props
  }: {
    href: string | { pathname?: string };
    children: React.ReactNode;
  }) =>
    React.createElement(
      "a",
      {
        href: typeof href === "string" ? href : href.pathname ?? "",
        ...props,
      },
      children,
    ),
}));

vi.mock("next/navigation", () => ({
  redirect: redirectMock,
  usePathname: () => getMockPathname(),
  useRouter: () => routerMock,
}));

vi.mock("next/headers", () => ({
  cookies: cookiesMock,
  headers: headersMock,
}));

vi.mock("server-only", () => ({}));
vi.mock("client-only", () => ({}));
