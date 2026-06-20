import type { AuthResponse, Operator } from "./types";

export {
  clearSession,
  clearSession as clearAuth,
  getAccessToken as getStoredToken,
  loadSession,
  saveSession,
} from "./session";

const OPERATOR_KEY = "agentnet_operator";

export function getStoredOperator(): Operator | null {
  if (typeof window === "undefined") {
    return null;
  }

  const raw = localStorage.getItem(OPERATOR_KEY);
  if (!raw) {
    return null;
  }

  try {
    return JSON.parse(raw) as Operator;
  } catch {
    return null;
  }
}

export function persistAuth(auth: AuthResponse): void {
  localStorage.setItem("agentnet_token", auth.access_token);
  localStorage.setItem(OPERATOR_KEY, JSON.stringify(auth.operator));
}

export function getStoredOperatorName(): string | null {
  return getStoredOperator()?.name ?? null;
}

export function isAuthenticated(): boolean {
  if (typeof window === "undefined") {
    return false;
  }
  return Boolean(localStorage.getItem("agentnet_token"));
}
