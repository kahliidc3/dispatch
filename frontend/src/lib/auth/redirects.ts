const authRoutes = new Set(["/login", "/mfa"]);

export function getSearchParamValue(
  value: string | string[] | undefined,
): string | null {
  if (Array.isArray(value)) {
    return value[0] ?? null;
  }

  return value ?? null;
}

export function sanitizeNextUrl(value: string | null | undefined) {
  if (!value || value.trim().length === 0) {
    return "/";
  }

  const normalized = value.trim();

  if (!normalized.startsWith("/") || normalized.startsWith("//")) {
    return "/";
  }

  const [pathname] = normalized.split("?");

  if (authRoutes.has(pathname)) {
    return "/";
  }

  return normalized;
}

export function buildLoginUrl(nextUrl?: string | null, reason?: string | null) {
  const sanitizedNextUrl = sanitizeNextUrl(nextUrl);
  const searchParams = new URLSearchParams();

  if (sanitizedNextUrl !== "/") {
    searchParams.set("next", sanitizedNextUrl);
  }

  if (reason) {
    searchParams.set("reason", reason);
  }

  const queryString = searchParams.toString();
  return queryString.length > 0 ? `/login?${queryString}` : "/login";
}

export function buildMfaUrl(nextUrl?: string | null) {
  const sanitizedNextUrl = sanitizeNextUrl(nextUrl);

  if (sanitizedNextUrl === "/") {
    return "/mfa";
  }

  return `/mfa?next=${encodeURIComponent(sanitizedNextUrl)}`;
}

export function getBrowserNextUrl() {
  if (typeof window === "undefined") {
    return "/";
  }

  return sanitizeNextUrl(
    `${window.location.pathname}${window.location.search}`,
  );
}

export function redirectToLoginInBrowser(nextUrl?: string | null) {
  if (typeof window === "undefined") {
    return;
  }

  window.location.assign(buildLoginUrl(nextUrl ?? getBrowserNextUrl()));
}
