"use client";

import { useMemo, useState } from "react";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { apiEndpoints } from "@/lib/api/endpoints";
import { clientJson } from "@/lib/api/client";
import { ApiError } from "@/lib/api/errors";
import { buildMfaUrl } from "@/lib/auth/redirects";
import type { SessionResponse } from "@/types/api";

const loginSchema = z.object({
  email: z.string().trim().email("Enter a valid work email."),
  password: z
    .string()
    .trim()
    .min(8, "Enter the password assigned for this operator account."),
});

type LoginFormProps = {
  nextUrl: string;
  reason: string | null;
};

type FieldErrors = Partial<Record<keyof z.infer<typeof loginSchema>, string>> & {
  form?: string;
};

export function LoginForm({ nextUrl, reason }: LoginFormProps) {
  const [email, setEmail] = useState("operator@dispatch.internal");
  const [password, setPassword] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errors, setErrors] = useState<FieldErrors>({});

  const reasonMessage = useMemo(() => {
    switch (reason) {
      case "challenge-expired":
        return "The verification step expired. Start a fresh sign-in to continue.";
      case "session-expired":
        return "Your session ended. Sign in again to reopen the console.";
      default:
        return null;
    }
  }, [reason]);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const parsed = loginSchema.safeParse({
      email,
      password,
    });

    if (!parsed.success) {
      const flattened = parsed.error.flatten().fieldErrors;
      setErrors({
        email: flattened.email?.[0],
        password: flattened.password?.[0],
      });
      return;
    }

    setIsSubmitting(true);
    setErrors({});

    try {
      const response = await clientJson<SessionResponse>(apiEndpoints.internal.session, {
        method: "POST",
        body: {
          ...parsed.data,
          nextUrl,
        },
        redirectOnUnauthorized: false,
      });

      if (response.status === "mfa_required") {
        window.location.assign(buildMfaUrl(response.challenge?.nextUrl ?? nextUrl));
        return;
      }

      window.location.assign(response.nextUrl ?? nextUrl);
    } catch (error) {
      if (error instanceof ApiError) {
        if (error.code === "rate_limited") {
          setErrors({
            form: "Sign-in unavailable - try again later.",
          });
        } else {
          setErrors({
            form: "Check your email or password and try again.",
          });
        }

        return;
      }

      setErrors({
        form: "Sign-in is temporarily unavailable.",
      });
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form className="page-stack" onSubmit={handleSubmit}>
      <header>
        <h1 className="page-title">Sign in</h1>
        <p className="page-description">
          Use your operator credentials first, then confirm the six-digit code
          from your authenticator app before the dashboard opens.
        </p>
      </header>
      {reasonMessage ? (
        <div className="surface-panel-muted p-4 text-sm text-text-muted">
          {reasonMessage}
        </div>
      ) : null}
      <div className="grid gap-4">
        <div>
          <label className="label" htmlFor="email">
            Email
          </label>
          <Input
            id="email"
            type="email"
            autoComplete="username"
            placeholder="operator@dispatch.internal"
            required
            value={email}
            onChange={(event) => {
              setEmail(event.target.value);
              setErrors((current) => ({
                ...current,
                email: undefined,
                form: undefined,
              }));
            }}
          />
          {errors.email ? (
            <p className="mt-2 text-sm text-danger">{errors.email}</p>
          ) : null}
        </div>
        <div>
          <label className="label" htmlFor="password">
            Password
          </label>
          <Input
            id="password"
            type="password"
            autoComplete="current-password"
            placeholder="********"
            required
            value={password}
            onChange={(event) => {
              setPassword(event.target.value);
              setErrors((current) => ({
                ...current,
                password: undefined,
                form: undefined,
              }));
            }}
          />
          {errors.password ? (
            <p className="mt-2 text-sm text-danger">{errors.password}</p>
          ) : null}
        </div>
      </div>
      <div className="surface-panel-muted p-4 text-sm text-text-muted">
        Sessions stay in httpOnly cookies only. Passwords, MFA codes, and API
        key secrets are never stored in browser storage.
      </div>
      {errors.form ? (
        <p className="text-sm text-danger" role="alert">
          {errors.form}
        </p>
      ) : null}
      <div className="flex flex-wrap gap-3">
        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting ? "Checking credentials..." : "Continue to verification"}
        </Button>
        <Button type="button" variant="outline" disabled>
          SSO placeholder
        </Button>
      </div>
    </form>
  );
}
