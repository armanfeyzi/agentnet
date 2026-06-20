import json
import uuid

import httpx
import pytest
from agentnet_shared.schemas.experience import ExperienceMetadata, ExperiencePost

from agentnet_mcp.client import AgentNetClient
from agentnet_mcp.config import AgentNetSettings
from agentnet_mcp.tools.draft_experience import (
    DraftExperienceValidationError,
    PENDING_APPROVAL_MESSAGE,
    submit_draft,
)


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


async def test_submit_draft_returns_pending_approval_message(settings: AgentNetSettings) -> None:
    draft_id = str(uuid.uuid4())
    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["method"] = request.method
        captured["path"] = request.url.path
        captured["headers"] = dict(request.headers)
        captured["body"] = json.loads(request.content)
        return httpx.Response(201, json={"draft_id": draft_id, "status": "pending_approval"})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url=settings.api_url) as http:
        client = AgentNetClient(settings, http_client=http)
        result = await submit_draft(client, _experience_payload())

    assert result == {
        "draft_id": draft_id,
        "status": "pending_approval",
        "message": PENDING_APPROVAL_MESSAGE,
    }
    assert captured["method"] == "POST"
    assert captured["path"] == "/experiences/draft"
    assert captured["headers"]["x-api-key"] == settings.api_key
    assert captured["headers"]["x-agent-id"] == settings.agent_id
    assert captured["body"]["task"] == "Deploy service"


async def test_submit_draft_validates_before_api_call(settings: AgentNetSettings) -> None:
    called = False

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal called
        called = True
        return httpx.Response(201, json={"draft_id": str(uuid.uuid4())})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url=settings.api_url) as http:
        client = AgentNetClient(settings, http_client=http)
        with pytest.raises(DraftExperienceValidationError):
            await submit_draft(client, {"task": ""})

    assert called is False
