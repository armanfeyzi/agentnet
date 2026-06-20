import type { AuthRequest, AuthResponse } from "@/lib/types";

async function authRequest(
  path: "login" | "register",
  payload: AuthRequest,
): Promise<AuthResponse> {
  const response = await fetch(`/api/auth/${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  const body = await response.json().catch(() => null);

  if (!response.ok) {
    const detail =
      typeof body?.detail === "string"
        ? body.detail
        : `Authentication failed (${response.status})`;
    throw new Error(detail);
  }

  return body as AuthResponse;
}

export async function login(payload: AuthRequest): Promise<AuthResponse> {
  return authRequest("login", payload);
}

export async function register(payload: AuthRequest): Promise<AuthResponse> {
  return authRequest("register", payload);
}

export async function loginOrRegisterWithCode(
  code: string,
): Promise<AuthResponse> {
  try {
    return await login({ code });
  } catch (error) {
    if (error instanceof Error && error.message.includes("not registered")) {
      return register({ code });
    }
    throw error;
  }
}

export function authHeaders(token: string): HeadersInit {
  return {
    Authorization: `Bearer ${token}`,
    "Content-Type": "application/json",
  };
}
