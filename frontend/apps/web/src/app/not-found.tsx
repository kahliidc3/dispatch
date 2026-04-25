import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function NotFound() {
  return (
    <main className="flex min-h-screen items-center justify-center px-6 py-12">
      <div className="surface-panel w-full max-w-lg p-8">
        <div className="page-stack">
          <header>
            <h1 className="page-title">Page not found</h1>
            <p className="page-description">
              The route exists in the scaffold, but this URL does not map to a
              current placeholder surface.
            </p>
          </header>
          <div className="flex flex-wrap gap-3">
            <Button asChild>
              <Link href="/">Return to dashboard</Link>
            </Button>
            <Button asChild variant="outline">
              <Link href="/login">Open login placeholder</Link>
            </Button>
          </div>
        </div>
      </div>
    </main>
  );
}
