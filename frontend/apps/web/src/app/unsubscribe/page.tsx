import { Suspense } from "react";
import type { Metadata } from "next";
import { UnsubscribeForm } from "./_components/unsubscribe-form";

export const metadata: Metadata = {
  title: "Unsubscribe",
  robots: { index: false, follow: false },
};

export default function UnsubscribePage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center p-6">
      <div className="w-full max-w-md">
        <div className="mb-8 text-center">
          <h1 className="text-xl font-semibold">Email preferences</h1>
          <p className="mt-1 text-sm text-text-muted">
            Manage your subscription to our emails.
          </p>
        </div>
        <Suspense
          fallback={
            <div className="surface-panel p-8 text-center text-sm text-text-muted">
              Loading…
            </div>
          }
        >
          <UnsubscribeForm />
        </Suspense>
      </div>
    </div>
  );
}
