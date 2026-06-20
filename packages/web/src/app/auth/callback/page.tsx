"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";

import { useAuth } from "@/contexts/auth-context";
import { loginOrRegisterWithCode } from "@/lib/auth-api";

function AuthCallbackContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { setSessionFromResponse } = useAuth();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const code = searchParams.get("code");
    const oauthError = searchParams.get("error");

    if (oauthError) {
      setError(`GitHub authorization failed: ${oauthError}`);
      return;
    }

    if (!code) {
      setError("Missing authorization code from GitHub.");
      return;
    }

    let cancelled = false;

    async function completeOAuth() {
      try {
        const response = await loginOrRegisterWithCode(code!);
        if (cancelled) {
          return;
        }
        setSessionFromResponse(response.access_token, response.operator);
        router.replace("/dashboard");
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Authentication failed");
        }
      }
    }

    void completeOAuth();

    return () => {
      cancelled = true;
    };
  }, [searchParams, router, setSessionFromResponse]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4">
      <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-8 text-center shadow-sm">
        {error ? (
          <>
            <p className="text-sm text-red-600">{error}</p>
            <Link
              href="/login"
              className="mt-4 inline-block text-sm font-medium text-slate-900 underline"
            >
              Back to login
            </Link>
          </>
        ) : (
          <p className="text-sm text-slate-600">Completing GitHub sign-in...</p>
        )}
      </div>
    </div>
  );
}

export default function AuthCallbackPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center text-sm text-slate-500">
          Loading...
        </div>
      }
    >
      <AuthCallbackContent />
    </Suspense>
  );
}
