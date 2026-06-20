export function getApiBaseUrl(): string {
  return (
    process.env.API_URL ??
    process.env.NEXT_PUBLIC_API_URL ??
    "http://localhost:8000"
  );
}

export function isAuthDevMode(): boolean {
  const value = process.env.NEXT_PUBLIC_AUTH_DEV_MODE ?? "false";
  return ["1", "true", "yes"].includes(value.toLowerCase());
}

export function getGitHubClientId(): string | undefined {
  const clientId = process.env.NEXT_PUBLIC_GITHUB_CLIENT_ID;
  return clientId && clientId.length > 0 ? clientId : undefined;
}

export function getGitHubOAuthUrl(redirectUri: string): string {
  const clientId = getGitHubClientId();
  if (!clientId) {
    throw new Error("NEXT_PUBLIC_GITHUB_CLIENT_ID is not configured");
  }

  const params = new URLSearchParams({
    client_id: clientId,
    redirect_uri: redirectUri,
    scope: "read:user user:email",
  });

  return `https://github.com/login/oauth/authorize?${params.toString()}`;
}
