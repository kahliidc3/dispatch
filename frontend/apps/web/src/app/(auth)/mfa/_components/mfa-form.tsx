"use client";

import { useRef, useState } from "react";
import { RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { apiEndpoints } from "@/lib/api/endpoints";
import { clientJson } from "@/lib/api/client";
import { ApiError } from "@/lib/api/errors";
import { buildLoginUrl } from "@/lib/auth/redirects";
import { formatTimestamp } from "@/lib/formatters";
import type { AuthChallengeSummary, SessionResponse } from "@/types/api";

type MfaFormProps = {
  challenge: AuthChallengeSummary;
  nextUrl: string;
};

export function MfaForm({ challenge, nextUrl }: MfaFormProps) {
  const [code, setCode] = useState("");
  const [formError, setFormError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isResetting, setIsResetting] = useState(false);
  const submittedCodeRef = useRef<string | null>(null);

  async function submitCode(nextCode: string) {
    if (nextCode.length !== 6 || isSubmitting || submittedCodeRef.current === nextCode) {
      return;
    }

    submittedCodeRef.current = nextCode;
    setIsSubmitting(true);
    setFormError(null);

    try {
      const response = await clientJson<SessionResponse>(apiEndpoints.internal.session, {
        method: "PUT",
        body: {
          code: nextCode,
          nextUrl,
        },
        redirectOnUnauthorized: false,
      });

      window.location.assign(response.nextUrl ?? nextUrl);
    } catch (error) {
      submittedCodeRef.current = null;

      if (error instanceof ApiError) {
        if (error.code === "challenge_expired") {
          window.location.assign(buildLoginUrl(nextUrl, "challenge-expired"));
          return;
        }

        if (error.code === "rate_limited") {
          setFormError("Verification unavailable - start again.");
          return;
        }

        setFormError("Code not accepted. Try a fresh code from your authenticator app.");
        setCode("");
        return;
      }

      setFormError("Verification is temporarily unavailable.");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleReset() {
    setIsResetting(true);

    try {
      await clientJson(apiEndpoints.internal.session, {
        method: "DELETE",
        redirectOnUnauthorized: false,
      });
    } finally {
      window.location.assign(buildLoginUrl(nextUrl));
    }
  }

  return (
    <form
      className="page-stack"
      onSubmit={(event) => {
        event.preventDefault();
        void submitCode(code);
      }}
    >
      <header>
        <h1 className="page-title">Verify sign in</h1>
        <p className="page-description">
          Enter the six digits from the authenticator app assigned to{" "}
          <span className="mono text-sm">{challenge.maskedEmail}</span>. This
          step expires at {formatTimestamp(challenge.expiresAt)}.
        </p>
      </header>
      <div className="surface-panel-muted grid gap-2 p-4 text-sm text-text-muted">
        <div className="flex items-center justify-between gap-3">
          <span>Challenge scope</span>
          <span className="mono text-xs">{challenge.nextUrl ?? "/"}</span>
        </div>
        <div className="flex items-center justify-between gap-3">
          <span>Paste support</span>
          <span>Leading zeros are preserved.</span>
        </div>
      </div>
      <div>
        <label className="label" htmlFor="mfa-code">
          Six-digit code
        </label>
        <Input
          id="mfa-code"
          inputMode="numeric"
          maxLength={6}
          placeholder="000000"
          autoComplete="one-time-code"
          className="mono text-center text-lg tracking-[0.45em]"
          value={code}
          onChange={(event) => {
            const nextCode = event.target.value.replace(/\D/g, "").slice(0, 6);

            setCode(nextCode);
            setFormError(null);

            if (nextCode.length === 6) {
              void submitCode(nextCode);
            }
          }}
        />
        <p className="mt-2 text-sm text-text-muted">
          Paste or type the raw six digits. Submission starts automatically once
          all six are present.
        </p>
      </div>
      {formError ? (
        <p className="text-sm text-danger" role="alert">
          {formError}
        </p>
      ) : null}
      <div className="flex flex-wrap gap-3">
        <Button type="submit" disabled={isSubmitting || code.length !== 6}>
          {isSubmitting ? "Checking code..." : "Verify code"}
        </Button>
        <Button
          type="button"
          variant="outline"
          disabled={isResetting}
          onClick={() => void handleReset()}
        >
          <RotateCcw className="h-4 w-4" />
          {isResetting ? "Resetting..." : "Start again"}
        </Button>
      </div>
    </form>
  );
}
