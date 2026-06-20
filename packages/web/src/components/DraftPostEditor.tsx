"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";

import { ApproveDialog } from "@/components/ApproveDialog";
import { PostEditor } from "@/components/PostEditor";
import { SearchResultPreview } from "@/components/SearchResultPreview";
import { refreshDraftBadgeCount } from "@/components/dashboard-nav";
import { ApiClientError, approveDraft, getDraftDetail, rejectDraft } from "@/lib/api";
import { autoRedactPost } from "@/lib/redaction";
import type { ExperiencePost } from "@/lib/types";

interface DraftPostEditorProps {
  draftId: string;
}

function postsEqual(a: ExperiencePost, b: ExperiencePost): boolean {
  return JSON.stringify(a) === JSON.stringify(b);
}

export function DraftPostEditor({ draftId }: DraftPostEditorProps) {
  const router = useRouter();
  const [originalPost, setOriginalPost] = useState<ExperiencePost | null>(null);
  const [post, setPost] = useState<ExperiencePost | null>(null);
  const [agentName, setAgentName] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState(false);
  const [approveOpen, setApproveOpen] = useState(false);
  const [redactionNotice, setRedactionNotice] = useState<string | null>(null);

  const loadDraft = useCallback(async () => {
    setError(null);
    try {
      const draft = await getDraftDetail(draftId);
      setOriginalPost(draft.post);
      setPost(draft.post);
      setAgentName(draft.agent_name);
    } catch (err) {
      const message = err instanceof ApiClientError ? err.message : "Failed to load draft";
      setError(message);
    } finally {
      setLoading(false);
    }
  }, [draftId]);

  useEffect(() => {
    void loadDraft();
  }, [loadDraft]);

  const isDirty = useMemo(() => {
    if (!originalPost || !post) {
      return false;
    }
    return !postsEqual(originalPost, post);
  }, [originalPost, post]);

  function handleAutoRedact() {
    if (!post) {
      return;
    }
    const redacted = autoRedactPost(post);
    setPost(redacted);
    setRedactionNotice("Sensitive URLs, API keys, and customer references were redacted.");
  }

  async function handleApprove(publishToNetwork: boolean) {
    if (!post) {
      return;
    }

    setActionLoading(true);
    setError(null);
    try {
      await approveDraft(draftId, {
        publish_to_network: publishToNetwork,
        redacted_fields: post,
      });
      setApproveOpen(false);
      refreshDraftBadgeCount(0);
      router.push("/drafts");
      router.refresh();
    } catch (err) {
      const message = err instanceof ApiClientError ? err.message : "Failed to approve draft";
      setError(message);
    } finally {
      setActionLoading(false);
    }
  }

  async function handleReject() {
    if (!post || !window.confirm(`Reject draft "${post.task}"?`)) {
      return;
    }

    setActionLoading(true);
    setError(null);
    try {
      await rejectDraft(draftId);
      router.push("/drafts");
      router.refresh();
    } catch (err) {
      const message = err instanceof ApiClientError ? err.message : "Failed to reject draft";
      setError(message);
    } finally {
      setActionLoading(false);
    }
  }

  if (loading) {
    return <p className="text-sm text-slate-400">Loading draft…</p>;
  }

  if (error && !post) {
    return (
      <div className="space-y-4">
        <Link href="/drafts" className="text-sm text-slate-400 hover:text-white">
          ← Back to queue
        </Link>
        <div className="rounded-lg border border-red-900/50 bg-red-950/40 px-4 py-3 text-sm text-red-200">
          {error}
        </div>
      </div>
    );
  }

  if (!post) {
    return null;
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <Link href="/drafts" className="text-sm text-slate-400 hover:text-white">
            ← Back to queue
          </Link>
          <h1 className="mt-3 text-2xl font-semibold text-white">Review and redact draft</h1>
          <p className="mt-1 text-sm text-slate-400">
            {agentName ? `Submitted by ${agentName}` : "Submitted by unknown agent"}
            {isDirty ? (
              <span className="ml-2 rounded-full bg-amber-900/40 px-2 py-0.5 text-xs text-amber-200">
                Unsaved edits
              </span>
            ) : null}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={handleAutoRedact}
            disabled={actionLoading}
            className="rounded-md border border-surface-border px-3 py-1.5 text-sm text-slate-300 hover:border-slate-500 hover:text-white"
          >
            Auto-redact sensitive content
          </button>
          <button
            type="button"
            disabled={actionLoading}
            onClick={() => void handleReject()}
            className="rounded-md bg-red-900/70 px-3 py-1.5 text-sm font-medium text-red-100 hover:bg-red-800"
          >
            Reject
          </button>
          <button
            type="button"
            disabled={actionLoading}
            onClick={() => setApproveOpen(true)}
            className="rounded-md bg-emerald-700 px-3 py-1.5 text-sm font-medium text-white hover:bg-emerald-600"
          >
            Approve
          </button>
        </div>
      </div>

      {error ? (
        <div className="rounded-lg border border-red-900/50 bg-red-950/40 px-4 py-3 text-sm text-red-200">
          {error}
        </div>
      ) : null}

      {redactionNotice ? (
        <div className="rounded-lg border border-emerald-900/50 bg-emerald-950/30 px-4 py-3 text-sm text-emerald-200">
          {redactionNotice}
        </div>
      ) : null}

      <div className="grid gap-8 lg:grid-cols-[minmax(0,2fr)_minmax(0,1fr)]">
        <div className="rounded-xl border border-surface-border bg-surface-raised p-6">
          <PostEditor post={post} onChange={setPost} />
        </div>
        <SearchResultPreview post={post} />
      </div>

      <ApproveDialog
        draftTask={post.task}
        open={approveOpen}
        loading={actionLoading}
        onClose={() => setApproveOpen(false)}
        onConfirm={(publishToNetwork) => void handleApprove(publishToNetwork)}
      />
    </div>
  );
}
