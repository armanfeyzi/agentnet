"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { ApproveDialog } from "@/components/ApproveDialog";
import { refreshDraftBadgeCount } from "@/components/dashboard-nav";
import { ApiClientError, approveDraft, listPendingDrafts, rejectDraft } from "@/lib/api";
import type { DraftQueueItem } from "@/lib/types";

function formatDate(iso: string): string {
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(iso));
}

export function DraftQueue() {
  const [drafts, setDrafts] = useState<DraftQueueItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionId, setActionId] = useState<string | null>(null);
  const [approveTarget, setApproveTarget] = useState<DraftQueueItem | null>(null);

  const loadDrafts = useCallback(async () => {
    setError(null);
    try {
      const data = await listPendingDrafts();
      setDrafts(data.drafts);
      refreshDraftBadgeCount(data.drafts.length);
    } catch (err) {
      const message =
        err instanceof ApiClientError ? err.message : "Failed to load drafts";
      setError(message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadDrafts();
  }, [loadDrafts]);

  async function handleReject(draft: DraftQueueItem) {
    if (!window.confirm(`Reject draft "${draft.task}"?`)) {
      return;
    }

    setActionId(draft.id);
    setError(null);
    try {
      await rejectDraft(draft.id);
      await loadDrafts();
    } catch (err) {
      const message =
        err instanceof ApiClientError ? err.message : "Failed to reject draft";
      setError(message);
    } finally {
      setActionId(null);
    }
  }

  async function handleApprove(publishToNetwork: boolean) {
    if (!approveTarget) {
      return;
    }

    setActionId(approveTarget.id);
    setError(null);
    try {
      await approveDraft(approveTarget.id, { publish_to_network: publishToNetwork });
      setApproveTarget(null);
      await loadDrafts();
    } catch (err) {
      const message =
        err instanceof ApiClientError ? err.message : "Failed to approve draft";
      setError(message);
    } finally {
      setActionId(null);
    }
  }

  if (loading) {
    return <p className="text-sm text-slate-500">Loading pending drafts…</p>;
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Draft approval queue</h1>
          <p className="mt-1 text-sm text-slate-600">
            Review agent-submitted experiences before they become searchable.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <span className="rounded-full border border-slate-200 bg-white px-3 py-1 text-sm text-slate-600">
            {drafts.length} pending
          </span>
          <button
            type="button"
            onClick={() => {
              setLoading(true);
              void loadDrafts();
            }}
            className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-50"
          >
            Refresh
          </button>
        </div>
      </div>

      {error ? (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      ) : null}

      {drafts.length === 0 ? (
        <div className="rounded-xl border border-dashed border-slate-200 bg-slate-50 px-6 py-12 text-center">
          <p className="text-base font-medium text-slate-800">No pending drafts</p>
          <p className="mt-2 text-sm text-slate-500">
            When agents submit experiences via MCP, they will appear here for approval.
          </p>
        </div>
      ) : (
        <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
          <table className="min-w-full divide-y divide-slate-200">
            <thead className="bg-slate-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Task
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Problem
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Agent
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Submitted
                </th>
                <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {drafts.map((draft) => {
                const busy = actionId === draft.id;
                return (
                  <tr key={draft.id} className="hover:bg-slate-50/80">
                    <td className="px-4 py-4 align-top">
                      <p className="max-w-xs text-sm font-medium text-slate-900">{draft.task}</p>
                    </td>
                    <td className="px-4 py-4 align-top">
                      <p className="max-w-md text-sm text-slate-600">{draft.problem_summary}</p>
                    </td>
                    <td className="px-4 py-4 align-top">
                      <p className="text-sm text-slate-700">
                        {draft.agent_name ?? "Unknown agent"}
                      </p>
                    </td>
                    <td className="px-4 py-4 align-top">
                      <p className="whitespace-nowrap text-sm text-slate-500">
                        {formatDate(draft.created_at)}
                      </p>
                    </td>
                    <td className="px-4 py-4 align-top">
                      <div className="flex justify-end gap-2">
                        <Link
                          href={`/drafts/${draft.id}/edit`}
                          className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-50"
                        >
                          Edit
                        </Link>
                        <button
                          type="button"
                          disabled={busy}
                          onClick={() => setApproveTarget(draft)}
                          className="rounded-lg bg-emerald-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-emerald-500"
                        >
                          Approve
                        </button>
                        <button
                          type="button"
                          disabled={busy}
                          onClick={() => void handleReject(draft)}
                          className="rounded-lg bg-red-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-red-500"
                        >
                          Reject
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      <ApproveDialog
        draftTask={approveTarget?.task ?? ""}
        open={approveTarget !== null}
        loading={actionId !== null}
        onClose={() => setApproveTarget(null)}
        onConfirm={(publishToNetwork) => void handleApprove(publishToNetwork)}
      />
    </div>
  );
}
