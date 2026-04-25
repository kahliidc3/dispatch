import { vi } from "vitest";

type RouterMock = {
  back: ReturnType<typeof vi.fn>;
  forward: ReturnType<typeof vi.fn>;
  prefetch: ReturnType<typeof vi.fn>;
  push: ReturnType<typeof vi.fn>;
  refresh: ReturnType<typeof vi.fn>;
  replace: ReturnType<typeof vi.fn>;
};

let pathname = "/";

export const routerMock: RouterMock = {
  back: vi.fn(),
  forward: vi.fn(),
  prefetch: vi.fn(),
  push: vi.fn(),
  refresh: vi.fn(),
  replace: vi.fn(),
};

export const redirectMock = vi.fn((href: string) => {
  throw new Error(`NEXT_REDIRECT:${href}`);
});

export function getMockPathname() {
  return pathname;
}

export function setMockPathname(nextPathname: string) {
  pathname = nextPathname;
}

export function resetNavigationMocks() {
  pathname = "/";
  redirectMock.mockClear();
  Object.values(routerMock).forEach((mock) => mock.mockReset());
}
