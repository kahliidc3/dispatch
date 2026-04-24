import { vi } from "vitest";

type CookieStore = {
  get: (name: string) => { value: string } | undefined;
  toString: () => string;
};

type HeaderStore = {
  get: (name: string) => string | null;
};

let cookieEntries = new Map<string, string>();
let headerEntries = new Headers();

export const cookiesMock = vi.fn<() => Promise<CookieStore>>(async () => ({
  get: (name: string) => {
    const value = cookieEntries.get(name);
    return value ? { value } : undefined;
  },
  toString: () =>
    Array.from(cookieEntries.entries())
      .map(([name, value]) => `${name}=${value}`)
      .join("; "),
}));

export const headersMock = vi.fn<() => Promise<HeaderStore>>(async () => ({
  get: (name: string) => headerEntries.get(name),
}));

export function setMockCookies(nextCookies: Record<string, string>) {
  cookieEntries = new Map(Object.entries(nextCookies));
}

export function setMockHeaders(nextHeaders: Record<string, string>) {
  headerEntries = new Headers(nextHeaders);
}

export function resetHeadersMocks() {
  cookieEntries = new Map();
  headerEntries = new Headers();
  cookiesMock.mockClear();
  headersMock.mockClear();
}
