from dataclasses import dataclass

import httpx
from fastapi import HTTPException, status

from agentnet_api.config import settings


@dataclass(frozen=True)
class GitHubUser:
    github_id: str
    name: str
    email: str | None


async def fetch_github_user(*, code: str | None = None, github_id: str | None = None, name: str | None = None, email: str | None = None) -> GitHubUser:
    if settings.auth_dev_mode:
        if not github_id or not name:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="github_id and name are required in AUTH_DEV_MODE",
            )
        return GitHubUser(github_id=github_id, name=name, email=email)

    if not code:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="code is required for GitHub OAuth login",
        )
    if not settings.github_client_id or not settings.github_client_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GitHub OAuth is not configured",
        )

    async with httpx.AsyncClient(timeout=10.0) as client:
        token_response = await client.post(
            "https://github.com/login/oauth/access_token",
            headers={"Accept": "application/json"},
            json={
                "client_id": settings.github_client_id,
                "client_secret": settings.github_client_secret,
                "code": code,
            },
        )
        token_response.raise_for_status()
        access_token = token_response.json().get("access_token")
        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid GitHub authorization code",
            )

        user_response = await client.get(
            "https://api.github.com/user",
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {access_token}",
            },
        )
        user_response.raise_for_status()
        user = user_response.json()

    return GitHubUser(
        github_id=str(user["id"]),
        name=user.get("name") or user.get("login") or "GitHub User",
        email=user.get("email"),
    )
