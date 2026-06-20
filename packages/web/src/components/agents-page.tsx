"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";

import { useAuth } from "@/contexts/auth-context";
import {
  ApiClientError,
  createAgent,
  createApiKey,
  deactivateAgent,
  listAgents,
} from "@/lib/api";
import type { Agent, ApiKeyResponse } from "@/lib/types";

function parseTags(input: string): string[] {
  return input
    .split(",")
    .map((tag) => tag.trim().toLowerCase())
    .filter(Boolean);
}

function CopyButton({ value, label }: { value: string; label: string }) {
  const [copied, setCopied] = useState(false);

  async function handleCopy() {
    await navigator.clipboard.writeText(value);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <button
      type="button"
      onClick={handleCopy}
      className="rounded border border-slate-300 px-2 py-1 text-xs text-slate-600 hover:bg-slate-50"
    >
      {copied ? "Copied" : label}
    </button>
  );
}

function McpConfigSnippet({ agentId, apiKey }: { agentId: string; apiKey?: string }) {
  const lines = [
    `AGENTNET_AGENT_ID=${agentId}`,
    ...(apiKey ? [`AGENTNET_API_KEY=${apiKey}`] : []),
  ];

  return (
    <pre className="overflow-x-auto rounded-lg bg-slate-900 p-3 text-xs text-slate-100">
      {lines.join("\n")}
    </pre>
  );
}

export function AgentsPage() {
  const { session } = useAuth();
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [name, setName] = useState("");
  const [modelFamily, setModelFamily] = useState("");
  const [capabilityTags, setCapabilityTags] = useState("");
  const [creating, setCreating] = useState(false);

  const [apiKeyName, setApiKeyName] = useState("Cursor MCP");
  const [generatingKey, setGeneratingKey] = useState(false);
  const [generatedKey, setGeneratedKey] = useState<ApiKeyResponse | null>(null);
  const [deactivatingId, setDeactivatingId] = useState<string | null>(null);

  const loadAgents = useCallback(async () => {
    const token = session?.accessToken;
    if (!token) return;

    setLoading(true);
    setError(null);
    try {
      const data = await listAgents(token);
      setAgents(data);
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : "Failed to load agents");
    } finally {
      setLoading(false);
    }
  }, [session?.accessToken]);

  useEffect(() => {
    void loadAgents();
  }, [loadAgents]);

  async function handleCreate(event: FormEvent) {
    event.preventDefault();
    const token = session?.accessToken;
    if (!token) return;

    setCreating(true);
    setError(null);
    try {
      await createAgent(token, {
        name: name.trim(),
        model_family: modelFamily.trim() || null,
        capability_tags: parseTags(capabilityTags),
        api_key_scope: "operator",
      });
      setName("");
      setModelFamily("");
      setCapabilityTags("");
      await loadAgents();
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : "Failed to create agent");
    } finally {
      setCreating(false);
    }
  }

  async function handleDeactivate(agentId: string, agentName: string) {
    if (!confirm(`Deactivate "${agentName}"? MCP tools will stop working for this agent.`)) {
      return;
    }

    const token = session?.accessToken;
    if (!token) return;

    setDeactivatingId(agentId);
    setError(null);
    try {
      await deactivateAgent(token, agentId);
      await loadAgents();
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : "Failed to deactivate agent");
    } finally {
      setDeactivatingId(null);
    }
  }

  async function handleGenerateApiKey(event: FormEvent) {
    event.preventDefault();
    const token = session?.accessToken;
    if (!token) return;

    setGeneratingKey(true);
    setError(null);
    try {
      const key = await createApiKey(token, apiKeyName.trim() || undefined);
      setGeneratedKey(key);
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : "Failed to generate API key");
    } finally {
      setGeneratingKey(false);
    }
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Agents</h1>
        <p className="mt-2 text-slate-600">
          Register agents for MCP access. Each agent gets a unique{" "}
          <code className="rounded bg-slate-100 px-1 text-sm">agent_id</code> for Cursor
          configuration.
        </p>
      </div>

      {error ? (
        <p className="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">{error}</p>
      ) : null}

      <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-medium text-slate-900">Create agent</h2>
        <form className="mt-4 grid gap-4 sm:grid-cols-2" onSubmit={handleCreate}>
          <label className="block text-sm font-medium text-slate-700">
            Name
            <input
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-100"
              placeholder="Cursor Dev Agent"
            />
          </label>

          <label className="block text-sm font-medium text-slate-700">
            Model family
            <input
              value={modelFamily}
              onChange={(e) => setModelFamily(e.target.value)}
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-100"
              placeholder="claude-sonnet"
            />
          </label>

          <label className="block text-sm font-medium text-slate-700 sm:col-span-2">
            Capability tags
            <input
              value={capabilityTags}
              onChange={(e) => setCapabilityTags(e.target.value)}
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-100"
              placeholder="fastapi, postgres, mcp"
            />
            <span className="mt-1 block text-xs text-slate-500">
              Comma-separated lowercase slugs (e.g. fastapi, postgres)
            </span>
          </label>

          <div className="sm:col-span-2">
            <button
              type="submit"
              disabled={creating}
              className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-50"
            >
              {creating ? "Creating…" : "Create agent"}
            </button>
          </div>
        </form>
      </section>

      <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-medium text-slate-900">Operator API key</h2>
        <p className="mt-1 text-sm text-slate-600">
          Generate an API key for MCP server authentication. The full key is shown once.
        </p>

        <form className="mt-4 flex flex-wrap items-end gap-3" onSubmit={handleGenerateApiKey}>
          <label className="block text-sm font-medium text-slate-700">
            Key name
            <input
              value={apiKeyName}
              onChange={(e) => setApiKeyName(e.target.value)}
              className="mt-1 w-56 rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-100"
              placeholder="Cursor MCP"
            />
          </label>
          <button
            type="submit"
            disabled={generatingKey}
            className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50"
          >
            {generatingKey ? "Generating…" : "Generate API key"}
          </button>
        </form>

        {generatedKey ? (
          <div className="mt-4 space-y-3 rounded-lg border border-amber-200 bg-amber-50 p-4">
            <p className="text-sm font-medium text-amber-900">
              Copy this key now — it will not be shown again.
            </p>
            <div className="flex items-center gap-2">
              <code className="flex-1 overflow-x-auto rounded bg-white px-3 py-2 text-sm text-slate-800">
                {generatedKey.api_key}
              </code>
              <CopyButton value={generatedKey.api_key} label="Copy key" />
            </div>
            <p className="text-xs text-amber-800">
              Prefix: {generatedKey.key_prefix} · Created{" "}
              {new Date(generatedKey.created_at).toLocaleString()}
            </p>
          </div>
        ) : null}
      </section>

      <section className="rounded-xl border border-slate-200 bg-white shadow-sm">
        <div className="border-b border-slate-200 px-6 py-4">
          <h2 className="text-lg font-medium text-slate-900">Your agents</h2>
        </div>

        {loading ? (
          <p className="px-6 py-8 text-sm text-slate-500">Loading agents…</p>
        ) : agents.length === 0 ? (
          <p className="px-6 py-8 text-sm text-slate-500">
            No active agents yet. Create one above to get started.
          </p>
        ) : (
          <ul className="divide-y divide-slate-200">
            {agents.map((agent) => (
              <li key={agent.id} className="px-6 py-5">
                <div className="flex flex-wrap items-start justify-between gap-4">
                  <div>
                    <h3 className="font-medium text-slate-900">{agent.name}</h3>
                    <p className="mt-1 text-sm text-slate-600">
                      {agent.model_family ?? "No model family"} ·{" "}
                      {agent.capability_tags.length > 0
                        ? agent.capability_tags.join(", ")
                        : "No tags"}
                    </p>
                  </div>
                  <button
                    type="button"
                    disabled={deactivatingId === agent.id}
                    onClick={() => void handleDeactivate(agent.id, agent.name)}
                    className="rounded-lg border border-red-200 px-3 py-1.5 text-sm text-red-700 hover:bg-red-50 disabled:opacity-50"
                  >
                    {deactivatingId === agent.id ? "Deactivating…" : "Deactivate"}
                  </button>
                </div>

                <div className="mt-4">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-medium uppercase tracking-wide text-slate-500">
                      Agent ID (MCP)
                    </span>
                    <CopyButton value={agent.id} label="Copy ID" />
                  </div>
                  <code className="mt-1 block text-sm text-slate-800">{agent.id}</code>
                </div>

                <div className="mt-4">
                  <p className="mb-2 text-xs font-medium uppercase tracking-wide text-slate-500">
                    MCP environment
                  </p>
                  <McpConfigSnippet
                    agentId={agent.id}
                    apiKey={generatedKey?.api_key}
                  />
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
