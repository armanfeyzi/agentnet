"use client";

import { useEffect, useState } from "react";

interface ApproveDialogProps {
  draftTask: string;
  open: boolean;
  loading: boolean;
  onClose: () => void;
  onConfirm: (publishToNetwork: boolean) => void;
}

export function ApproveDialog({
  draftTask,
  open,
  loading,
  onClose,
  onConfirm,
}: ApproveDialogProps) {
  const [publishToNetwork, setPublishToNetwork] = useState(false);

  useEffect(() => {
    if (open) {
      setPublishToNetwork(false);
    }
  }, [open]);

  if (!open) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="approve-dialog-title"
        className="w-full max-w-md rounded-xl border border-slate-200 bg-white p-6 shadow-xl"
      >
        <h2 id="approve-dialog-title" className="text-lg font-semibold text-slate-900">
          Approve draft
        </h2>
        <p className="mt-2 text-sm text-slate-600">
          Approve <span className="font-medium text-slate-900">{draftTask}</span> so your agents
          can search and reuse it.
        </p>

        <label className="mt-4 flex cursor-pointer items-start gap-3 rounded-lg border border-slate-200 p-3">
          <input
            type="checkbox"
            checked={publishToNetwork}
            onChange={(event) => setPublishToNetwork(event.target.checked)}
            className="mt-1 h-4 w-4 rounded border-slate-300 accent-brand-600"
          />
          <span>
            <span className="block text-sm font-medium text-slate-900">Publish to network</span>
            <span className="mt-1 block text-xs text-slate-500">
              {publishToNetwork
                ? "Public: visible on the public feed for all agents and human readers."
                : "Private: searchable only by your organization's agents."}
            </span>
          </span>
        </label>

        <div className="mt-6 flex justify-end gap-3">
          <button
            type="button"
            onClick={onClose}
            disabled={loading}
            className="rounded-lg px-4 py-2 text-sm text-slate-600 hover:text-slate-900"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={() => onConfirm(publishToNetwork)}
            disabled={loading}
            className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-500"
          >
            {loading ? "Approving…" : publishToNetwork ? "Approve & publish" : "Approve (private)"}
          </button>
        </div>
      </div>
    </div>
  );
}
