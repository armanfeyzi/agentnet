import type { PublicFeedResponse } from "@/lib/types";

export interface PublicFeedParams {
  limit?: number;
  offset?: number;
  q?: string;
  capability_tags?: string[];
}

function getServerApiBaseUrl(): string {
  return (
    process.env.API_URL ??
    process.env.NEXT_PUBLIC_API_URL ??
    "http://localhost:8000"
  );
}

export async function fetchPublicFeed(
  params: PublicFeedParams = {},
): Promise<PublicFeedResponse> {
  const { limit = 20, offset = 0, q, capability_tags = [] } = params;

  const searchParams = new URLSearchParams();
  searchParams.set("limit", String(limit));
  searchParams.set("offset", String(offset));

  if (q) {
    searchParams.set("q", q);
  }

  for (const tag of capability_tags) {
    searchParams.append("capability_tags", tag);
  }

  const url = `${getServerApiBaseUrl()}/experiences/public?${searchParams.toString()}`;
  const response = await fetch(url, {
    next: { revalidate: 60 },
  });

  if (!response.ok) {
    throw new Error(`Failed to load public feed (${response.status})`);
  }

  return response.json() as Promise<PublicFeedResponse>;
}
