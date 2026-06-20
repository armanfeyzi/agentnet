import { AppNav } from "@/components/app-nav";
import { RequireAuth } from "@/components/require-auth";

export default function DashboardLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <RequireAuth>
      <div className="min-h-screen bg-slate-50">
        <AppNav />
        <main className="mx-auto max-w-6xl px-6 py-8">{children}</main>
      </div>
    </RequireAuth>
  );
}
