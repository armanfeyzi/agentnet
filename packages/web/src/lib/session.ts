import type { AuthSession } from "@/lib/types";

const TOKEN_KEY = "agentnet_token";
const OPERATOR_KEY = "agentnet_operator";

export function loadSession(): AuthSession | null {
  if (typeof window === "undefined") {
    return null;
  }

  const accessToken = localStorage.getItem(TOKEN_KEY);
  const operatorRaw = localStorage.getItem(OPERATOR_KEY);

  if (!accessToken || !operatorRaw) {
    return null;
  }

  try {
    return {
      accessToken,
      operator: JSON.parse(operatorRaw),
    };
  } catch {
    clearSession();
    return null;
  }
}

export function saveSession(session: AuthSession): void {
  localStorage.setItem(TOKEN_KEY, session.accessToken);
  localStorage.setItem(OPERATOR_KEY, JSON.stringify(session.operator));
}

export function clearSession(): void {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(OPERATOR_KEY);
}

export function getAccessToken(): string | null {
  if (typeof window === "undefined") {
    return null;
  }
  return localStorage.getItem(TOKEN_KEY);
}
