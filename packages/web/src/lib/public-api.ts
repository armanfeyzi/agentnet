import type { PublicAgentProfile, PublicExperienceDetail } from "@/lib/types";

function getServerApiBaseUrl(): string {
  return process.env.API_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
}

export async function fetchPublicExperience(
  experienceId: string,
): Promise<PublicExperienceDetail | null> {
  const response = await fetch(`${getServerApiBaseUrl()}/experiences/${experienceId}`, {
    next: { revalidate: 60 },
  });

  if (response.status === 404) {
    return null;
  }

  if (!response.ok) {
    throw new Error(`Failed to load experience (${response.status})`);
  }

  return response.json() as Promise<PublicExperienceDetail>;
}

export async function fetchPublicAgentProfile(
  agentId: string,
): Promise<PublicAgentProfile | null> {
  const response = await fetch(`${getServerApiBaseUrl()}/agents/${agentId}/public`, {
    next: { revalidate: 60 },
  });

  if (response.status === 404) {
    return null;
  }

  if (!response.ok) {
    throw new Error(`Failed to load agent profile (${response.status})`);
  }

  return response.json() as Promise<PublicAgentProfile>;
}
