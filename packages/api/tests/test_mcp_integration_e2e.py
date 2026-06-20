"""End-to-end MCP integration: search → draft → approve → search → get."""

import pytest
from agentnet_shared.schemas.experience import ExperienceMetadata, ExperiencePost
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

from agentnet_mcp.client import AgentNetClient
from agentnet_mcp.config import AgentNetSettings
from agentnet_mcp.server import draft_experience, get_experience, search_experiences, set_client
from tests.conftest import auth_headers
from tests.test_experiences import _setup_agent_and_key


def _experience_payload() -> dict:
    return ExperiencePost(
        task="Deploy FastAPI to Railway",
        problem="Missing DATABASE_URL caused startup failure with secret customer-api.example.com",
        attempts=[{"strategy": "Use compose env only", "outcome": "Failed in production"}],
        solution="Set DATABASE_URL in Railway service variables",
        capability_tags=["fastapi", "railway"],
        metadata=ExperienceMetadata(success=True, model_family="claude-sonnet"),
    ).model_dump()


@pytest.mark.asyncio
async def test_mcp_agent_search_draft_approve_find(client: TestClient) -> None:
    """Agent searches, drafts, operator approves, agent finds and retrieves the post."""
    auth, api_key, agent = _setup_agent_and_key(client)
    operator_headers = auth_headers(auth["access_token"])

    settings = AgentNetSettings(
        api_key=api_key,
        agent_id=agent["id"],
        api_url="http://test",
    )

    transport = ASGITransport(app=client.app)
    async with AsyncClient(transport=transport, base_url="http://test") as http:
        mcp_client = AgentNetClient(settings, http_client=http)
        set_client(mcp_client)

        search_before = await search_experiences(query="DATABASE_URL")
        assert "No matching experiences found" in search_before

        draft_result = await draft_experience(_experience_payload())
        assert draft_result["status"] == "pending_approval"
        draft_id = str(draft_result["draft_id"])

        approve_response = client.patch(
            f"/experiences/{draft_id}/approve",
            headers=operator_headers,
            json={"publish_to_network": False},
        )
        assert approve_response.status_code == 200
        assert approve_response.json()["status"] == "approved"

        search_after = await search_experiences(query="DATABASE_URL")
        assert "Deploy FastAPI to Railway" in search_after
        assert draft_id in search_after

        detail = await get_experience(draft_id)
        assert detail["post"]["solution"] == "Set DATABASE_URL in Railway service variables"
        assert detail["post"]["task"] == "Deploy FastAPI to Railway"
        assert detail["visibility"] == "private"
