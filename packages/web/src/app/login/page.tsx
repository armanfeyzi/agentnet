"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";

import { useAuth } from "@/contexts/auth-context";
import { getGitHubOAuthUrl, isAuthDevMode } from "@/lib/config";

export default function LoginPage() {
  const router = useRouter();
  const { session, isLoading, signIn, signUp } = useAuth();
  const devMode = isAuthDevMode();

  const [githubId, setGithubId] = useState("");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!isLoading && session) {
      router.replace("/dashboard");
    }
  }, [isLoading, session, router]);

  async function handleDevAuth(mode: "login" | "register") {
    setError(null);
    setSubmitting(true);

    try {
      const payload = {
        github_id: githubId.trim(),
        name: name.trim(),
        email: email.trim() || undefined,
      };

      if (mode === "login") {
        await signIn(payload);
      } else {
        await signUp(payload);
      }

      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Authentication failed");
    } finally {
      setSubmitting(false);
    }
  }

  function handleDevSubmit(
    event: FormEvent<HTMLFormElement>,
    mode: "login" | "register",
  ) {
    event.preventDefault();
    void handleDevAuth(mode);
  }

  function handleGitHubSignIn() {
    setError(null);

    try {
      const redirectUri = `${window.location.origin}/auth/callback`;
      window.location.href = getGitHubOAuthUrl(redirectUri);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "GitHub OAuth is unavailable",
      );
    }
  }

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center text-sm text-slate-500">
        Loading...
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4">
      <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
        <div className="mb-8 text-center">
          <Link href="/" className="text-xl font-semibold text-slate-900">
            AgentNet
          </Link>
          <p className="mt-2 text-sm text-slate-600">
            Sign in to manage agents and approve experience drafts.
          </p>
        </div>

        {error ? (
          <div className="mb-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        ) : null}

        {devMode ? (
          <form
            className="space-y-4"
            onSubmit={(event) => handleDevSubmit(event, "login")}
          >
            <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
              Dev mode enabled. Use github_id and name without real GitHub OAuth.
            </div>

            <div>
              <label
                htmlFor="github_id"
                className="block text-sm font-medium text-slate-700"
              >
                GitHub ID
              </label>
              <input
                id="github_id"
                type="text"
                required
                value={githubId}
                onChange={(event) => setGithubId(event.target.value)}
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none ring-slate-400 focus:ring-2"
                placeholder="dev-user-1"
              />
            </div>

            <div>
              <label
                htmlFor="name"
                className="block text-sm font-medium text-slate-700"
              >
                Name
              </label>
              <input
                id="name"
                type="text"
                required
                value={name}
                onChange={(event) => setName(event.target.value)}
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none ring-slate-400 focus:ring-2"
                placeholder="Dev Operator"
              />
            </div>

            <div>
              <label
                htmlFor="email"
                className="block text-sm font-medium text-slate-700"
              >
                Email (optional)
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none ring-slate-400 focus:ring-2"
                placeholder="you@example.com"
              />
            </div>

            <div className="flex gap-3 pt-2">
              <button
                type="submit"
                disabled={submitting}
                className="flex-1 rounded-lg bg-slate-900 px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-slate-800 disabled:opacity-60"
              >
                Sign in
              </button>
              <button
                type="button"
                disabled={submitting}
                onClick={() => void handleDevAuth("register")}
                className="flex-1 rounded-lg border border-slate-300 px-4 py-2.5 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50 disabled:opacity-60"
              >
                Register
              </button>
            </div>
          </form>
        ) : (
          <button
            type="button"
            onClick={handleGitHubSignIn}
            className="flex w-full items-center justify-center gap-2 rounded-lg bg-slate-900 px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-slate-800"
          >
            Sign in with GitHub
          </button>
        )}
      </div>
    </div>
  );
}
