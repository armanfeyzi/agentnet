import { getApiBaseUrl } from "@/lib/config";
import type { AuthRequest } from "@/lib/types";
import { NextResponse } from "next/server";

async function proxyAuth(
  path: "login" | "register",
  payload: AuthRequest,
): Promise<NextResponse> {
  const response = await fetch(`${getApiBaseUrl()}/auth/${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  const body = await response.json().catch(() => ({
    detail: "Unexpected response from authentication service",
  }));

  return NextResponse.json(body, { status: response.status });
}

export async function POST(request: Request) {
  const payload = (await request.json()) as AuthRequest;
  return proxyAuth("register", payload);
}
