import Link from "next/link";

export default function AuthLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <main className="flex min-h-screen items-center justify-center px-6 py-12">
      <div className="surface-panel w-full max-w-md p-8">
        <div className="page-stack">
          <Link
            href="/"
            className="text-sm font-medium text-[color:var(--text-muted)]"
          >
            Dispatch
          </Link>
          {children}
        </div>
      </div>
    </main>
  );
}
