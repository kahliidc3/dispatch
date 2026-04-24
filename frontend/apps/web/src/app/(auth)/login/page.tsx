import { redirect } from "next/navigation";
import {
  buildMfaUrl,
  getSearchParamValue,
  sanitizeNextUrl,
} from "@/lib/auth/redirects";
import { getResolvedSession } from "@/lib/auth/session";
import { LoginForm } from "./_components/login-form";

type LoginPageProps = {
  searchParams: Promise<{
    next?: string | string[];
    reason?: string | string[];
  }>;
};

export default async function LoginPage({ searchParams }: LoginPageProps) {
  const params = await searchParams;
  const nextUrl = sanitizeNextUrl(getSearchParamValue(params.next));
  const reason = getSearchParamValue(params.reason);
  const resolvedSession = await getResolvedSession();

  if (resolvedSession.status === "authenticated") {
    redirect(nextUrl);
  }

  if (resolvedSession.status === "mfa_required") {
    redirect(buildMfaUrl(resolvedSession.challenge?.nextUrl ?? nextUrl));
  }

  return <LoginForm nextUrl={nextUrl} reason={reason} />;
}
