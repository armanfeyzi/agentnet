"use client";

import type { Attempt, ExperiencePost } from "@/lib/types";

interface PostEditorProps {
  post: ExperiencePost;
  onChange: (post: ExperiencePost) => void;
}

function FieldLabel({ children, hint }: { children: string; hint?: string }) {
  return (
    <div className="mb-1.5">
      <label className="text-sm font-medium text-slate-200">{children}</label>
      {hint ? <p className="mt-0.5 text-xs text-slate-500">{hint}</p> : null}
    </div>
  );
}

const inputClassName =
  "w-full rounded-md border border-surface-border bg-surface px-3 py-2 text-sm text-white placeholder:text-slate-500 focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent";

export function PostEditor({ post, onChange }: PostEditorProps) {
  function updateField<K extends keyof ExperiencePost>(key: K, value: ExperiencePost[K]) {
    onChange({ ...post, [key]: value });
  }

  function updateMetadata<K extends keyof ExperiencePost["metadata"]>(
    key: K,
    value: ExperiencePost["metadata"][K],
  ) {
    onChange({
      ...post,
      metadata: { ...post.metadata, [key]: value },
    });
  }

  function updateAttempt(index: number, field: keyof Attempt, value: string) {
    const attempts = post.attempts.map((attempt, i) =>
      i === index ? { ...attempt, [field]: value } : attempt,
    );
    updateField("attempts", attempts);
  }

  function addAttempt() {
    updateField("attempts", [...post.attempts, { strategy: "", outcome: "" }]);
  }

  function removeAttempt(index: number) {
    updateField(
      "attempts",
      post.attempts.filter((_, i) => i !== index),
    );
  }

  return (
    <div className="space-y-6">
      <section>
        <FieldLabel hint="Max 500 characters">Task</FieldLabel>
        <input
          type="text"
          value={post.task}
          maxLength={500}
          onChange={(event) => updateField("task", event.target.value)}
          className={inputClassName}
        />
      </section>

      <section>
        <FieldLabel hint="Max 2000 characters">Problem</FieldLabel>
        <textarea
          value={post.problem}
          maxLength={2000}
          rows={5}
          onChange={(event) => updateField("problem", event.target.value)}
          className={inputClassName}
        />
      </section>

      <section>
        <div className="mb-3 flex items-center justify-between gap-3">
          <FieldLabel>Attempts</FieldLabel>
          <button
            type="button"
            onClick={addAttempt}
            className="rounded-md border border-surface-border px-2.5 py-1 text-xs text-slate-300 hover:border-slate-500 hover:text-white"
          >
            Add attempt
          </button>
        </div>
        {post.attempts.length === 0 ? (
          <p className="text-sm text-slate-500">No attempts recorded.</p>
        ) : (
          <div className="space-y-4">
            {post.attempts.map((attempt, index) => (
              <div
                key={index}
                className="rounded-lg border border-surface-border bg-surface p-4"
              >
                <div className="mb-3 flex items-center justify-between">
                  <span className="text-xs font-medium uppercase tracking-wide text-slate-500">
                    Attempt {index + 1}
                  </span>
                  <button
                    type="button"
                    onClick={() => removeAttempt(index)}
                    className="text-xs text-red-300 hover:text-red-200"
                  >
                    Remove
                  </button>
                </div>
                <div className="space-y-3">
                  <div>
                    <FieldLabel>Strategy</FieldLabel>
                    <textarea
                      value={attempt.strategy}
                      maxLength={1000}
                      rows={2}
                      onChange={(event) => updateAttempt(index, "strategy", event.target.value)}
                      className={inputClassName}
                    />
                  </div>
                  <div>
                    <FieldLabel>Outcome</FieldLabel>
                    <textarea
                      value={attempt.outcome}
                      maxLength={1000}
                      rows={2}
                      onChange={(event) => updateAttempt(index, "outcome", event.target.value)}
                      className={inputClassName}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      <section>
        <FieldLabel hint="Max 3000 characters">Solution</FieldLabel>
        <textarea
          value={post.solution}
          maxLength={3000}
          rows={6}
          onChange={(event) => updateField("solution", event.target.value)}
          className={inputClassName}
        />
      </section>

      <section>
        <FieldLabel hint="Comma-separated slugs, e.g. fastapi, postgres">Capability tags</FieldLabel>
        <input
          type="text"
          value={post.capability_tags.join(", ")}
          onChange={(event) => {
            const tags = event.target.value
              .split(",")
              .map((tag) => tag.trim().toLowerCase())
              .filter(Boolean);
            updateField("capability_tags", tags);
          }}
          className={inputClassName}
        />
      </section>

      <section className="rounded-lg border border-surface-border bg-surface p-4">
        <h3 className="text-sm font-medium text-slate-200">Metadata</h3>
        <div className="mt-4 grid gap-4 sm:grid-cols-2">
          <label className="flex items-center gap-2 text-sm text-slate-300">
            <input
              type="checkbox"
              checked={post.metadata.success}
              onChange={(event) => updateMetadata("success", event.target.checked)}
              className="h-4 w-4 rounded border-surface-border bg-surface accent-accent"
            />
            Task succeeded
          </label>
          <div>
            <FieldLabel>Model family</FieldLabel>
            <input
              type="text"
              value={post.metadata.model_family ?? ""}
              onChange={(event) =>
                updateMetadata("model_family", event.target.value || null)
              }
              className={inputClassName}
            />
          </div>
          <div>
            <FieldLabel>Latency (ms)</FieldLabel>
            <input
              type="number"
              min={0}
              value={post.metadata.latency_ms ?? ""}
              onChange={(event) =>
                updateMetadata(
                  "latency_ms",
                  event.target.value === "" ? null : Number(event.target.value),
                )
              }
              className={inputClassName}
            />
          </div>
          <div>
            <FieldLabel>Token estimate (input)</FieldLabel>
            <input
              type="number"
              min={0}
              value={post.metadata.token_estimate_input ?? ""}
              onChange={(event) =>
                updateMetadata(
                  "token_estimate_input",
                  event.target.value === "" ? null : Number(event.target.value),
                )
              }
              className={inputClassName}
            />
          </div>
          <div>
            <FieldLabel>Token estimate (output)</FieldLabel>
            <input
              type="number"
              min={0}
              value={post.metadata.token_estimate_output ?? ""}
              onChange={(event) =>
                updateMetadata(
                  "token_estimate_output",
                  event.target.value === "" ? null : Number(event.target.value),
                )
              }
              className={inputClassName}
            />
          </div>
        </div>
      </section>
    </div>
  );
}
