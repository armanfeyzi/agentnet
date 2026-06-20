import json
import uuid

import httpx
import pytest
from agentnet_shared.schemas.experience import ExperienceMetadata, ExperiencePost

from agentnet_mcp.client import AgentNetAPIError, AgentNetClient
from agentnet_mcp.config import AgentNetSettings


@pytest.fixture
def settings() -> AgentNetSettings:
    return AgentNetSettings(
        api_key="test-api-key",
        agent_id="11111111-1111-1111-1111-111111111111",
        api_url="http://agentnet.test",
    )


def _experience_post() -> ExperiencePost:
    return ExperiencePost(
        task="Deploy service",
        problem="Health check failed",
        solution="Set DATABASE_URL in Railway",
        capability_tags=["deployment"],
        metadata=ExperienceMetadata(success=True),
    )


async def test_search_experiences(settings: AgentNetSettings) -> None:
    captured: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/experiences/search"
        captured["q"] = request.url.params.get("q", "")
        captured["tags"] = request.url.params.get_list("tags")
        captured["tools"] = request.url.params.get_list("tools")
        captured["scope"] = request.url.params.get("scope", "")
        captured["limit"] = request.url.params.get("limit", "")
        assert request.headers["X-API-Key"] == settings.api_key
        assert request.headers["X-Agent-ID"] == settings.agent_id
        return httpx.Response(
            200,
            json={
                "results": [
                    {
                        "id": "22222222-2222-2222-2222-222222222222",
                        "task": "Deploy service",
                        "problem_summary": "Health check failed",
                        "capability_tags": ["deployment"],
                        "success": True,
                        "visibility": "private",
                    }
                ],
                "total": 1,
            },
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url=settings.api_url) as http:
        client = AgentNetClient(settings, http_client=http)
        result = await client.search_experiences(
            query="health check",
            tags=["deployment"],
            tools=["railway"],
            limit=5,
            scope="public",
        )

    assert captured["q"] == "health check"
    assert captured["tags"] == ["deployment"]
    assert captured["tools"] == ["railway"]
    assert captured["scope"] == "public"
    assert captured["limit"] == "5"
    assert len(result.results) == 1
    assert result.results[0].task == "Deploy service"


async def test_draft_experience(settings: AgentNetSettings) -> None:
    draft_id = str(uuid.uuid4())

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/experiences/draft"
        body = json.loads(request.content)
        assert body["task"] == "Deploy service"
        assert body["capability_tags"] == ["deployment"]
        return httpx.Response(
            201,
            json={"draft_id": draft_id, "status": "pending_approval"},
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url=settings.api_url) as http:
        client = AgentNetClient(settings, http_client=http)
        result = await client.draft_experience(_experience_post())

    assert result["draft_id"] == draft_id
    assert result["status"] == "pending_approval"


async def test_get_experience(settings: AgentNetSettings) -> None:
    experience_id = str(uuid.uuid4())
    full_post = {
        "task": "Deploy service",
        "problem": "Health check failed",
        "attempts": [],
        "solution": "Set DATABASE_URL in Railway",
        "capability_tags": ["deployment"],
        "metadata": {"success": True, "model_family": None},
    }

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == f"/experiences/{experience_id}"
        assert request.headers["X-API-Key"] == settings.api_key
        assert request.headers["X-Agent-ID"] == settings.agent_id
        return httpx.Response(
            200,
            json={
                "id": experience_id,
                "visibility": "public",
                "approved_at": "2026-06-20T12:00:00Z",
                "created_at": "2026-06-20T11:00:00Z",
                "post": full_post,
            },
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url=settings.api_url) as http:
        client = AgentNetClient(settings, http_client=http)
        result = await client.get_experience(experience_id)

    assert result["id"] == experience_id
    assert result["post"] == full_post


async def test_get_experience_forbidden(settings: AgentNetSettings) -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(403, json={"detail": "Forbidden"})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url=settings.api_url) as http:
        client = AgentNetClient(settings, http_client=http)
        with pytest.raises(AgentNetAPIError) as exc_info:
            await client.get_experience(str(uuid.uuid4()))

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Forbidden"


async def test_api_error_raises(settings: AgentNetSettings) -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"detail": "Experience not found"})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url=settings.api_url) as http:
        client = AgentNetClient(settings, http_client=http)
        with pytest.raises(AgentNetAPIError) as exc_info:
            await client.get_experience(str(uuid.uuid4()))

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Experience not found"
