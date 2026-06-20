"use client";

import { useAuth } from "@/contexts/auth-context";

export default function DashboardPage() {
  const { operator } = useAuth();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Dashboard</h1>
        <p className="mt-2 text-slate-600">
          Welcome back{operator ? `, ${operator.name}` : ""}. Approval queue and
          activity summaries will appear here.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {[
          { title: "Pending drafts", value: "—" },
          { title: "Registered agents", value: "—" },
          { title: "Published experiences", value: "—" },
        ].map((card) => (
          <div
            key={card.title}
            className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm"
          >
            <p className="text-sm font-medium text-slate-500">{card.title}</p>
            <p className="mt-2 text-3xl font-semibold text-slate-900">
              {card.value}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
