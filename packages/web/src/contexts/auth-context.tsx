"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { useRouter } from "next/navigation";

import { login, register } from "@/lib/auth-api";
import { clearSession, loadSession, saveSession } from "@/lib/session";
import type { AuthRequest, AuthSession, Operator } from "@/lib/types";

interface AuthContextValue {
  session: AuthSession | null;
  operator: Operator | null;
  isLoading: boolean;
  signIn: (payload: AuthRequest) => Promise<void>;
  signUp: (payload: AuthRequest) => Promise<void>;
  signOut: () => void;
  setSessionFromResponse: (accessToken: string, operator: Operator) => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const router = useRouter();
  const [session, setSession] = useState<AuthSession | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    setSession(loadSession());
    setIsLoading(false);
  }, []);

  const setSessionFromResponse = useCallback(
    (accessToken: string, operator: Operator) => {
      const nextSession = { accessToken, operator };
      saveSession(nextSession);
      setSession(nextSession);
    },
    [],
  );

  const signIn = useCallback(
    async (payload: AuthRequest) => {
      const response = await login(payload);
      setSessionFromResponse(response.access_token, response.operator);
    },
    [setSessionFromResponse],
  );

  const signUp = useCallback(
    async (payload: AuthRequest) => {
      const response = await register(payload);
      setSessionFromResponse(response.access_token, response.operator);
    },
    [setSessionFromResponse],
  );

  const signOut = useCallback(() => {
    clearSession();
    setSession(null);
    router.push("/login");
  }, [router]);

  const value = useMemo<AuthContextValue>(
    () => ({
      session,
      operator: session?.operator ?? null,
      isLoading,
      signIn,
      signUp,
      signOut,
      setSessionFromResponse,
    }),
    [session, isLoading, signIn, signUp, signOut, setSessionFromResponse],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}
