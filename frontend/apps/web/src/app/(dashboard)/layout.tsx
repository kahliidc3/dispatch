import { getResolvedSession } from "@/lib/auth/session";
import { requireUser } from "@/lib/auth/guards";
import { Sidebar } from "./_components/sidebar";
import { Topbar } from "./_components/topbar";

export default async function DashboardLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const session = await requireUser();
  const { source } = await getResolvedSession();

  return (
    <div className="app-shell">
      <Sidebar session={session} />
      <div className="app-main">
        <Topbar session={session} source={source} />
        <main className="content-area">{children}</main>
      </div>
    </div>
  );
}
