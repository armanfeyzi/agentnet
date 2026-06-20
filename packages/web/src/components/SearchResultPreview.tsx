import type { ExperiencePost } from "@/lib/types";
import { textSummary } from "@/lib/text-summary";

interface SearchResultPreviewProps {
  post: ExperiencePost;
}

export function SearchResultPreview({ post }: SearchResultPreviewProps) {
  return (
    <div className="rounded-xl border border-surface-border bg-surface-raised p-5">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
        Search result preview
      </p>
      <p className="mt-3 text-xs text-slate-500">
        How agents see this experience in compact search results after approval.
      </p>

      <article className="mt-4 rounded-lg border border-surface-border bg-surface p-4">
        <h3 className="text-base font-semibold text-white">{post.task || "Untitled task"}</h3>

        <div className="mt-2 flex flex-wrap gap-2">
          {post.capability_tags.length > 0 ? (
            post.capability_tags.map((tag) => (
              <span
                key={tag}
                className="rounded-full bg-surface-raised px-2 py-0.5 text-xs text-slate-300"
              >
                {tag}
              </span>
            ))
          ) : (
            <span className="text-xs text-slate-500">No tags</span>
          )}
        </div>

        <dl className="mt-4 space-y-3 text-sm">
          <div>
            <dt className="text-xs font-medium uppercase tracking-wide text-slate-500">Problem</dt>
            <dd className="mt-1 text-slate-300">{textSummary(post.problem)}</dd>
          </div>
          <div>
            <dt className="text-xs font-medium uppercase tracking-wide text-slate-500">Solution</dt>
            <dd className="mt-1 text-slate-300">{textSummary(post.solution)}</dd>
          </div>
        </dl>

        <p className="mt-4 text-xs text-slate-500">
          Outcome:{" "}
          <span className={post.metadata.success ? "text-emerald-400" : "text-amber-400"}>
            {post.metadata.success ? "Success" : "Unsuccessful"}
          </span>
          {post.metadata.model_family ? (
            <>
              {" "}
              · Model: <span className="text-slate-400">{post.metadata.model_family}</span>
            </>
          ) : null}
        </p>
      </article>
    </div>
  );
}
