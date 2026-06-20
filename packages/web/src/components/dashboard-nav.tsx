"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { useAuth } from "@/contexts/auth-context";
import { listPendingDrafts } from "@/lib/api";

const navItems = [
  { href: "/dashboard", label: "Dashboard", exact: true },
  { href: "/dashboard/agents", label: "Agents" },
  { href: "/dashboard/drafts", label: "Drafts", badge: true },
  { href: "/dashboard/settings", label: "Settings" },
];

export function refreshDraftBadgeCount(count: number) {
  window.dispatchEvent(new CustomEvent("draft-count-updated", { detail: { count } }));
}

export function DashboardNav() {
  const pathname = usePathname();
  const { operator, signOut, session } = useAuth();
  const [pendingCount, setPendingCount] = useState<number | null>(null);

  useEffect(() => {
    if (!session) {
      return;
    }

    let cancelled = false;

    async function loadCount() {
      try {
        const data = await listPendingDrafts();
        if (!cancelled) {
          setPendingCount(data.drafts.length);
        }
      } catch {
        if (!cancelled) {
          setPendingCount(null);
        }
      }
    }

    void loadCount();

    function handleCountUpdate(event: Event) {
      const custom = event as CustomEvent<{ count: number }>;
      if (typeof custom.detail?.count === "number") {
        setPendingCount(custom.detail.count);
      }
    }

    window.addEventListener("draft-count-updated", handleCountUpdate);
    const interval = window.setInterval(() => void loadCount(), 30_000);

    return () => {
      cancelled = true;
      window.removeEventListener("draft-count-updated", handleCountUpdate);
      window.clearInterval(interval);
    };
  }, [pathname, session]);

  return (
    <header className="border-b border-slate-200 bg-white">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-6 px-4 py-4">
        <div className="flex items-center gap-8">
          <Link href="/dashboard" className="text-lg font-semibold text-brand-700">
            AgentNet
          </Link>
          <nav className="flex gap-1">
            {navItems.map((item) => {
              const active = item.exact
                ? pathname === item.href
                : pathname.startsWith(item.href);

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                    active
                      ? "bg-brand-50 text-brand-700"
                      : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
                  }`}
                >
                  {item.label}
                  {item.badge && pendingCount !== null && pendingCount > 0 ? (
                    <span className="ml-2 inline-flex min-w-5 items-center justify-center rounded-full bg-brand-600 px-1.5 py-0.5 text-xs font-semibold text-white">
                      {pendingCount}
                    </span>
                  ) : null}
                </Link>
              );
            })}
          </nav>
        </div>
        <div className="flex items-center gap-4">
          {operator ? (
            <span className="text-sm text-slate-600">{operator.name}</span>
          ) : null}
          <button
            type="button"
            onClick={signOut}
            className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-50"
          >
            Sign out
          </button>
        </div>
      </div>
    </header>
  );
}

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const { isLoading, session } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !session) {
      router.replace("/login");
    }
  }, [isLoading, session, router]);

  if (isLoading || !session) {
    return (
      <main className="flex min-h-screen items-center justify-center">
        <p className="text-sm text-slate-500">Loading…</p>
      </main>
    );
  }

  return <>{children}</>;
}
