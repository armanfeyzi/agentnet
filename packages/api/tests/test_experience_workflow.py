import uuid

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from agentnet_api.db.models import Experience, ExperienceStatus, ExperienceVisibility
from tests.conftest import auth_headers, register_operator
from tests.test_experiences import _setup_agent_and_key


def _draft_payload(**overrides) -> dict:
    payload = {
        "task": "Deploy FastAPI to Railway",
        "problem": "Missing DATABASE_URL caused startup failure with secret customer-api.example.com",
        "attempts": [{"strategy": "Use compose env only", "outcome": "Failed in production"}],
        "solution": "Set DATABASE_URL in Railway service variables",
        "capability_tags": ["fastapi", "railway"],
        "metadata": {"success": True, "model_family": "claude-sonnet"},
    }
    payload.update(overrides)
    return payload


def _submit_draft(client: TestClient, api_key: str, agent_id: str, payload: dict | None = None) -> dict:
    response = client.post(
        "/experiences/draft",
        headers={"X-API-Key": api_key, "X-Agent-ID": agent_id},
        json=payload or _draft_payload(),
    )
    assert response.status_code == 201
    return response.json()


def test_list_pending_drafts_empty(client: TestClient):
    auth = register_operator(client)

    response = client.get("/experiences/drafts", headers=auth_headers(auth["access_token"]))

    assert response.status_code == 200
    assert response.json()["drafts"] == []


def test_list_pending_drafts_returns_queue(client: TestClient):
    auth, api_key, agent = _setup_agent_and_key(client)
    operator_headers = auth_headers(auth["access_token"])

    draft = _submit_draft(client, api_key, agent["id"])

    response = client.get("/experiences/drafts", headers=operator_headers)

    assert response.status_code == 200
    drafts = response.json()["drafts"]
    assert len(drafts) == 1
    assert drafts[0]["id"] == draft["draft_id"]
    assert drafts[0]["task"] == "Deploy FastAPI to Railway"
    assert drafts[0]["agent_name"] == "Test Agent"
    assert "customer-api.example.com" in drafts[0]["problem_summary"]


def test_approve_draft_private(client: TestClient, db_session: Session):
    auth, api_key, agent = _setup_agent_and_key(client)
    operator_headers = auth_headers(auth["access_token"])
    draft = _submit_draft(client, api_key, agent["id"])

    response = client.patch(
        f"/experiences/{draft['draft_id']}/approve",
        headers=operator_headers,
        json={"publish_to_network": False},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "approved"
    assert body["visibility"] == "private"
    assert body["approved_at"] is not None

    experience = db_session.get(Experience, uuid.UUID(draft["draft_id"]))
    assert experience.status == ExperienceStatus.approved
    assert experience.visibility == ExperienceVisibility.private


def test_approve_draft_public(client: TestClient, db_session: Session):
    auth, api_key, agent = _setup_agent_and_key(client)
    operator_headers = auth_headers(auth["access_token"])
    draft = _submit_draft(client, api_key, agent["id"])

    response = client.patch(
        f"/experiences/{draft['draft_id']}/approve",
        headers=operator_headers,
        json={"publish_to_network": True},
    )

    assert response.status_code == 200
    assert response.json()["visibility"] == "public"

    experience = db_session.get(Experience, uuid.UUID(draft["draft_id"]))
    assert experience.visibility == ExperienceVisibility.public


def test_approve_with_redacted_fields(client: TestClient, db_session: Session):
    auth, api_key, agent = _setup_agent_and_key(client)
    operator_headers = auth_headers(auth["access_token"])
    draft = _submit_draft(client, api_key, agent["id"])

    redacted = _draft_payload(
        problem="Missing DATABASE_URL caused startup failure with [REDACTED]",
        solution="Set DATABASE_URL in platform service variables",
        capability_tags=["fastapi", "deployment"],
    )

    response = client.patch(
        f"/experiences/{draft['draft_id']}/approve",
        headers=operator_headers,
        json={"publish_to_network": False, "redacted_fields": redacted},
    )

    assert response.status_code == 200

    experience = db_session.get(Experience, uuid.UUID(draft["draft_id"]))
    assert experience.problem == redacted["problem"]
    assert experience.content["problem"] == redacted["problem"]
    assert {tag.slug for tag in experience.tags} == {"fastapi", "deployment"}


def test_reject_draft(client: TestClient, db_session: Session):
    auth, api_key, agent = _setup_agent_and_key(client)
    operator_headers = auth_headers(auth["access_token"])
    draft = _submit_draft(client, api_key, agent["id"])

    response = client.patch(
        f"/experiences/{draft['draft_id']}/reject",
        headers=operator_headers,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "rejected"
    assert response.json()["visibility"] is None

    experience = db_session.get(Experience, uuid.UUID(draft["draft_id"]))
    assert experience.status == ExperienceStatus.rejected


def test_operator_cannot_approve_other_operators_draft(client: TestClient):
    _, api_key, agent = _setup_agent_and_key(client)
    draft = _submit_draft(client, api_key, agent["id"])

    other_auth = register_operator(client, github_id=f"other-{uuid.uuid4().hex[:8]}")
    response = client.patch(
        f"/experiences/{draft['draft_id']}/approve",
        headers=auth_headers(other_auth["access_token"]),
        json={"publish_to_network": False},
    )

    assert response.status_code == 404


def test_cannot_approve_already_approved_draft(client: TestClient):
    auth, api_key, agent = _setup_agent_and_key(client)
    operator_headers = auth_headers(auth["access_token"])
    draft = _submit_draft(client, api_key, agent["id"])

    client.patch(
        f"/experiences/{draft['draft_id']}/approve",
        headers=operator_headers,
        json={"publish_to_network": False},
    )

    response = client.patch(
        f"/experiences/{draft['draft_id']}/approve",
        headers=operator_headers,
        json={"publish_to_network": False},
    )

    assert response.status_code == 404
