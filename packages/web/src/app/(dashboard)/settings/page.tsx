"use client";

import { useAuth } from "@/contexts/auth-context";

export default function SettingsPage() {
  const { operator } = useAuth();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Settings</h1>
        <p className="mt-2 text-slate-600">
          Operator profile and API key settings.
        </p>
      </div>

      {operator ? (
        <div className="max-w-lg rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <dl className="space-y-4 text-sm">
            <div>
              <dt className="font-medium text-slate-500">Name</dt>
              <dd className="mt-1 text-slate-900">{operator.name}</dd>
            </div>
            <div>
              <dt className="font-medium text-slate-500">Email</dt>
              <dd className="mt-1 text-slate-900">
                {operator.email ?? "Not set"}
              </dd>
            </div>
            <div>
              <dt className="font-medium text-slate-500">GitHub ID</dt>
              <dd className="mt-1 text-slate-900">
                {operator.github_id ?? "Not set"}
              </dd>
            </div>
          </dl>
        </div>
      ) : null}
    </div>
  );
}
