import { getStoredToken } from "@/lib/auth";
import type {
  Agent,
  AgentListResponse,
  AgentRegistration,
  ApproveExperienceRequest,
  ApiError,
  ApiKeyResponse,
  AuthResponse,
  DraftDetailResponse,
  DraftQueueResponse,
  ExperienceActionResponse,
} from "./types";

const API_BASE = "/backend";

export class ApiClientError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiClientError";
    this.status = status;
  }
}

type ApiErrorBody = ApiError;

function formatErrorDetail(detail: ApiErrorBody["detail"]): string {
  if (!detail) return "Request failed";
  if (typeof detail === "string") return detail;
  return detail.map((item) => item.msg).join(", ");
}

async function apiFetch<T>(
  path: string,
  options: RequestInit & { token?: string | null } = {},
): Promise<T> {
  const { token, headers, ...rest } = options;
  const response = await fetch(`${API_BASE}${path}`, {
    ...rest,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...headers,
    },
  });

  if (!response.ok) {
    let message = response.statusText;
    try {
      const body = (await response.json()) as ApiErrorBody;
      message = formatErrorDetail(body.detail);
    } catch {
      // ignore JSON parse errors
    }
    throw new ApiClientError(message, response.status);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

export async function registerOperator(payload: {
  github_id: string;
  name: string;
  email?: string;
}): Promise<AuthResponse> {
  return apiFetch<AuthResponse>("/auth/register", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function loginOperator(payload: {
  github_id: string;
  name: string;
  email?: string;
}): Promise<AuthResponse> {
  return apiFetch<AuthResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function listAgents(token: string): Promise<Agent[]> {
  const data = await apiFetch<AgentListResponse>("/agents", { token });
  return data.agents;
}

export async function createAgent(
  token: string,
  payload: AgentRegistration,
): Promise<Agent> {
  return apiFetch<Agent>("/agents", {
    method: "POST",
    token,
    body: JSON.stringify(payload),
  });
}

export async function deactivateAgent(token: string, agentId: string): Promise<Agent> {
  return apiFetch<Agent>(`/agents/${agentId}`, {
    method: "DELETE",
    token,
  });
}

export async function createApiKey(
  token: string,
  name?: string,
): Promise<ApiKeyResponse> {
  return apiFetch<ApiKeyResponse>("/operators/me/api-keys", {
    method: "POST",
    token,
    body: JSON.stringify({ name: name || null }),
  });
}

function requireToken(): string {
  const token = getStoredToken();
  if (!token) {
    throw new ApiClientError("Not authenticated", 401);
  }
  return token;
}

export async function listPendingDrafts(): Promise<DraftQueueResponse> {
  return apiFetch<DraftQueueResponse>("/experiences/drafts", {
    token: requireToken(),
  });
}

export async function getDraftDetail(draftId: string): Promise<DraftDetailResponse> {
  return apiFetch<DraftDetailResponse>(`/experiences/drafts/${draftId}`, {
    token: requireToken(),
  });
}

export async function approveDraft(
  draftId: string,
  payload: ApproveExperienceRequest,
): Promise<ExperienceActionResponse> {
  return apiFetch<ExperienceActionResponse>(`/experiences/${draftId}/approve`, {
    method: "PATCH",
    token: requireToken(),
    body: JSON.stringify(payload),
  });
}

export async function rejectDraft(draftId: string): Promise<ExperienceActionResponse> {
  return apiFetch<ExperienceActionResponse>(`/experiences/${draftId}/reject`, {
    method: "PATCH",
    token: requireToken(),
  });
}
