from typing import Any, Literal

import httpx

from agentnet_shared.schemas.experience import ExperiencePost

from agentnet_mcp.config import AgentNetSettings
from agentnet_mcp.schemas import SearchExperiencesResponse


class AgentNetAPIError(Exception):
    """Raised when the AgentNet API returns an error response."""

    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"AgentNet API error {status_code}: {detail}")


class AgentNetClient:
    """HTTP client for the AgentNet REST API."""

    def __init__(
        self,
        settings: AgentNetSettings | None = None,
        *,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self._settings = settings or AgentNetSettings()
        self._http_client = http_client
        self._owns_client = http_client is None

    def _get_client(self) -> httpx.AsyncClient:
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(
                base_url=self._settings.api_url.rstrip("/"),
                timeout=30.0,
            )
        return self._http_client

    async def search_experiences(
        self,
        *,
        query: str | None = None,
        tags: list[str] | None = None,
        tools: list[str] | None = None,
        limit: int = 10,
        scope: Literal["org", "public"] = "org",
    ) -> SearchExperiencesResponse:
        params: list[tuple[str, str | int]] = [("scope", scope), ("limit", limit)]
        if query:
            params.append(("q", query))
        if tags:
            params.extend(("tags", tag) for tag in tags)
        if tools:
            params.extend(("tools", tool) for tool in tools)

        response = await self._get_client().get(
            "/experiences/search",
            headers=self._settings.auth_headers,
            params=params,
        )
        body = self._parse_response(response)
        if "items" in body and "results" not in body:
            body = {**body, "results": body["items"]}
        return SearchExperiencesResponse.model_validate(body)

    async def draft_experience(self, payload: ExperiencePost) -> dict[str, Any]:
        response = await self._get_client().post(
            "/experiences/draft",
            headers=self._settings.auth_headers,
            json=payload.model_dump(),
        )
        return self._parse_response(response)

    async def get_experience(self, experience_id: str) -> dict[str, Any]:
        response = await self._get_client().get(
            f"/experiences/{experience_id}",
            headers=self._settings.auth_headers,
        )
        return self._parse_response(response)

    async def aclose(self) -> None:
        if self._owns_client and self._http_client is not None:
            await self._http_client.aclose()
            self._http_client = None

    @staticmethod
    def _parse_response(response: httpx.Response) -> dict[str, Any]:
        try:
            body = response.json()
        except ValueError:
            body = {"detail": response.text or response.reason_phrase}

        if response.is_error:
            detail = body.get("detail", body) if isinstance(body, dict) else str(body)
            if not isinstance(detail, str):
                detail = str(detail)
            raise AgentNetAPIError(response.status_code, detail)

        if isinstance(body, dict):
            return body
        return {"result": body}
