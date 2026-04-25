export type UserRole = "admin" | "user";
export type AuthState = "anonymous" | "mfa_required" | "authenticated";

export type HealthResponse = {
  service: "web";
  status: "ok";
  requestId?: string | null;
};

export type SessionSource = "backend" | "dev";

export type SessionUser = {
  id: string;
  email: string;
  name: string;
  role: UserRole;
};

export type AuthChallengeSummary = {
  maskedEmail: string;
  expiresAt: string;
  nextUrl: string | null;
};

export type SessionResponse = {
  status: AuthState;
  session: SessionUser | null;
  source: SessionSource | null;
  challenge: AuthChallengeSummary | null;
  nextUrl: string | null;
};

export type ApiErrorCode =
  | "unauthorized"
  | "forbidden"
  | "not_found"
  | "conflict"
  | "rate_limited"
  | "validation_error"
  | "mfa_required"
  | "challenge_expired"
  | "invalid_credentials"
  | "unknown_error";

export type ApiErrorEnvelope = {
  error: {
    code: ApiErrorCode | string;
    message: string;
    details?: Record<string, unknown> | null;
  };
  requestId?: string | null;
};

export type ApiKeyStatus = "active" | "revoked";

export type ApiKeyRecord = {
  id: string;
  name: string;
  prefix: string;
  last4: string;
  createdAt: string;
  lastUsedAt: string | null;
  revokedAt: string | null;
  status: ApiKeyStatus;
};

export type UserStatus = "active" | "disabled";
export type UserMfaState = "enrolled" | "not_enrolled" | "reset_required";

export type SettingsUserRecord = {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  status: UserStatus;
  lastLoginAt: string | null;
  mfaState: UserMfaState;
};
