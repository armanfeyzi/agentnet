import json
import uuid

import httpx
import pytest
from agentnet_shared.schemas.experience import ExperienceMetadata, ExperiencePost
from mcp.server.fastmcp.exceptions import ToolError

from agentnet_mcp.client import AgentNetClient
from agentnet_mcp.config import AgentNetSettings
from agentnet_mcp.server import (
    SEARCH_EXPERIENCES_DESCRIPTION,
    draft_experience,
    get_experience,
    mcp,
    search_experiences,
    set_client,
)
from agentnet_mcp.summaries import format_search_results
from agentnet_mcp.schemas import ExperienceSummary, SearchExperiencesResponse


@pytest.fixture
def settings() -> AgentNetSettings:
    return AgentNetSettings(
        api_key="test-api-key",
        agent_id="11111111-1111-1111-1111-111111111111",
        api_url="http://agentnet.test",
    )


def _experience_payload() -> dict:
    return ExperiencePost(
        task="Deploy service",
        problem="Health check failed",
        solution="Set DATABASE_URL in Railway",
        capability_tags=["deployment"],
        metadata=ExperienceMetadata(success=True),
    ).model_dump()


def test_registers_three_tools() -> None:
    tool_names = {tool.name for tool in mcp._tool_manager.list_tools()}

    assert tool_names == {
        "search_experiences",
        "draft_experience",
        "get_experience",
    }


def test_search_experiences_tool_description() -> None:
    tools = {tool.name: tool for tool in mcp._tool_manager.list_tools()}
    description = tools["search_experiences"].description or ""

    assert description == SEARCH_EXPERIENCES_DESCRIPTION
    assert "before starting a new task" in description


async def test_search_experiences_tool(settings: AgentNetSettings) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/experiences/search"
        assert request.url.params["q"] == "deployment"
        assert request.url.params["scope"] == "org"
        return httpx.Response(
            200,
            json={
                "results": [
                    {
                        "id": "1",
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
        set_client(AgentNetClient(settings, http_client=http))
        result = await search_experiences(query="deployment")

    assert "Found 1 experience(s)" in result
    assert "[1]" in result
    assert "Deploy service" in result


def test_format_search_results_empty() -> None:
    assert format_search_results(SearchExperiencesResponse()) == "No matching experiences found."


def test_format_search_results_includes_summary_fields() -> None:
    response = SearchExperiencesResponse(
        results=[
            ExperienceSummary(
                id="abc",
                task="Fix auth",
                problem_summary="401 on draft endpoint",
                capability_tags=["auth"],
                success=False,
                visibility="public",
            )
        ],
        total=1,
    )

    formatted = format_search_results(response)
    assert "Fix auth" in formatted
    assert "401 on draft endpoint" in formatted
    assert "Success: no" in formatted
    assert "Visibility: public" in formatted


async def test_search_experiences_tool_api_error(settings: AgentNetSettings) -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(429, json={"detail": "Rate limit exceeded"})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url=settings.api_url) as http:
        set_client(AgentNetClient(settings, http_client=http))
        with pytest.raises(ToolError, match="429"):
            await search_experiences(query="anything")


async def test_draft_experience_tool(settings: AgentNetSettings) -> None:
    draft_id = str(uuid.uuid4())

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        assert body["task"] == "Deploy service"
        assert request.headers["X-API-Key"] == settings.api_key
        assert request.headers["X-Agent-ID"] == settings.agent_id
        return httpx.Response(201, json={"draft_id": draft_id, "status": "pending_approval"})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url=settings.api_url) as http:
        set_client(AgentNetClient(settings, http_client=http))
        result = await draft_experience(_experience_payload())

    assert result["draft_id"] == draft_id
    assert result["status"] == "pending_approval"
    assert "pending operator approval" in result["message"].lower()


async def test_get_experience_tool(settings: AgentNetSettings) -> None:
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
        assert request.url.path == f"/experiences/{experience_id}"
        return httpx.Response(200, json={"id": experience_id, "post": full_post})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url=settings.api_url) as http:
        set_client(AgentNetClient(settings, http_client=http))
        result = await get_experience(experience_id)

    assert result["id"] == experience_id
    assert result["post"] == full_post


async def test_get_experience_tool_not_found(settings: AgentNetSettings) -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"detail": "Experience not found"})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url=settings.api_url) as http:
        set_client(AgentNetClient(settings, http_client=http))
        with pytest.raises(ToolError, match="Experience not found"):
            await get_experience(str(uuid.uuid4()))


async def test_get_experience_tool_forbidden(settings: AgentNetSettings) -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(403, json={"detail": "Forbidden"})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url=settings.api_url) as http:
        set_client(AgentNetClient(settings, http_client=http))
        with pytest.raises(ToolError, match="Access denied"):
            await get_experience(str(uuid.uuid4()))


async def test_draft_experience_validation_error(settings: AgentNetSettings) -> None:
    set_client(AgentNetClient(settings))
    with pytest.raises(Exception, match="Invalid experience payload"):
        await draft_experience({"task": ""})
