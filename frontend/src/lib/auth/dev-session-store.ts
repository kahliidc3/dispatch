import "server-only";

const MAX_LOGIN_FAILURES = 5;
const LOGIN_LOCKOUT_WINDOW_MS = 5 * 60 * 1000;

type LoginAttemptState = {
  failures: number;
  lockedUntil: number | null;
};

declare global {
  var __dispatchDevLoginAttemptStore: Map<string, LoginAttemptState> | undefined;
}

function getStore() {
  globalThis.__dispatchDevLoginAttemptStore ??= new Map();
  return globalThis.__dispatchDevLoginAttemptStore;
}

function toKey(email: string) {
  return email.trim().toLowerCase();
}

export function getLoginLockout(email: string) {
  const entry = getStore().get(toKey(email));

  if (!entry?.lockedUntil) {
    return null;
  }

  const retryAfterMs = entry.lockedUntil - Date.now();

  if (retryAfterMs <= 0) {
    getStore().delete(toKey(email));
    return null;
  }

  return Math.max(Math.ceil(retryAfterMs / 1000), 1);
}

export function clearLoginFailures(email: string) {
  getStore().delete(toKey(email));
}

export function registerLoginFailure(email: string) {
  const key = toKey(email);
  const retryAfterSeconds = getLoginLockout(key);

  if (retryAfterSeconds) {
    return {
      locked: true,
      retryAfterSeconds,
    } as const;
  }

  const nextFailures = (getStore().get(key)?.failures ?? 0) + 1;
  const locked = nextFailures >= MAX_LOGIN_FAILURES;

  getStore().set(key, {
    failures: nextFailures,
    lockedUntil: locked ? Date.now() + LOGIN_LOCKOUT_WINDOW_MS : null,
  });

  return {
    locked,
    retryAfterSeconds: locked
      ? Math.ceil(LOGIN_LOCKOUT_WINDOW_MS / 1000)
      : null,
  } as const;
}

export function resetDevLoginAttemptStore() {
  getStore().clear();
}
