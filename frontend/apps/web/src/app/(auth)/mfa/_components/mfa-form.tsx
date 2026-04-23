import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export function MfaForm() {
  return (
    <form className="page-stack">
      <header>
        <h1 className="page-title">Verify sign in</h1>
        <p className="page-description">
          MFA input, challenge handling, and retry behavior are deferred to
          Sprint 02. This placeholder locks the route and field contract.
        </p>
      </header>
      <div>
        <label className="label" htmlFor="mfa-code">
          Six-digit code
        </label>
        <Input
          id="mfa-code"
          inputMode="numeric"
          maxLength={6}
          placeholder="000000"
        />
      </div>
      <div className="flex flex-wrap gap-3">
        <Button type="button">Verify</Button>
        <Button type="button" variant="outline">
          Resend placeholder
        </Button>
      </div>
    </form>
  );
}
