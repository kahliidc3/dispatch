import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export function LoginForm() {
  return (
    <form className="page-stack">
      <header>
        <h1 className="page-title">Sign in</h1>
        <p className="page-description">
          Authentication flows are scaffolded in Sprint 00. This page reserves
          the route, layout, and field structure for Sprint 02.
        </p>
      </header>
      <div className="grid gap-4">
        <div>
          <label className="label" htmlFor="email">
            Email
          </label>
          <Input
            id="email"
            type="email"
            placeholder="operator@dispatch.internal"
          />
        </div>
        <div>
          <label className="label" htmlFor="password">
            Password
          </label>
          <Input id="password" type="password" placeholder="********" />
        </div>
      </div>
      <div className="flex flex-wrap gap-3">
        <Button type="button">Continue</Button>
        <Button type="button" variant="outline">
          SSO placeholder
        </Button>
      </div>
    </form>
  );
}
