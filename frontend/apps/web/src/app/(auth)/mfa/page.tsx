import { redirect } from "next/navigation";
import {
  buildLoginUrl,
  getSearchParamValue,
  sanitizeNextUrl,
} from "@/lib/auth/redirects";
import { getResolvedSession } from "@/lib/auth/session";
import { MfaForm } from "./_components/mfa-form";

type MfaPageProps = {
  searchParams: Promise<{
    next?: string | string[];
  }>;
};

export default async function MfaPage({ searchParams }: MfaPageProps) {
  const params = await searchParams;
  const nextUrl = sanitizeNextUrl(getSearchParamValue(params.next));
  const resolvedSession = await getResolvedSession();

  if (resolvedSession.status === "authenticated") {
    redirect(nextUrl);
  }

  if (resolvedSession.status !== "mfa_required" || !resolvedSession.challenge) {
    redirect(buildLoginUrl(nextUrl, "challenge-expired"));
  }

  return <MfaForm challenge={resolvedSession.challenge} nextUrl={nextUrl} />;
}
