import uuid
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from agentnet_api.db.models import (
    ApiUsageEvent,
    ApiUsageEventType,
    Experience,
    ExperienceStatus,
    ExperienceVisibility,
)
from agentnet_api.experiences.service import resolve_capability_tags
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


def _approve(
    client: TestClient,
    operator_token: str,
    draft_id: str,
    *,
    publish_to_network: bool = False,
) -> None:
    response = client.patch(
        f"/experiences/{draft_id}/approve",
        headers=auth_headers(operator_token),
        json={"publish_to_network": publish_to_network},
    )
    assert response.status_code == 200


def _agent_headers(api_key: str, agent_id: str) -> dict[str, str]:
    return {"X-API-Key": api_key, "X-Agent-ID": agent_id}


def test_public_search_returns_only_public_approved(client: TestClient, db_session: Session):
    auth, api_key, agent = _setup_agent_and_key(client)
    operator_headers = auth_headers(auth["access_token"])

    private_draft = _submit_draft(
        client,
        api_key,
        agent["id"],
        _draft_payload(task="Private org task", capability_tags=["python"]),
    )
    public_draft = _submit_draft(
        client,
        api_key,
        agent["id"],
        _draft_payload(task="Public network task", capability_tags=["docker"]),
    )
    _approve(client, auth["access_token"], private_draft["draft_id"], publish_to_network=False)
    _approve(client, auth["access_token"], public_draft["draft_id"], publish_to_network=True)

    response = client.get("/experiences/search", params={"scope": "public"})

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert len(body["items"]) == 1
    assert body["items"][0]["task"] == "Public network task"
    assert body["items"][0]["visibility"] == "public"
    assert "post" not in body["items"][0]
    assert "solution" not in body["items"][0]


def test_public_search_full_text_query(client: TestClient):
    auth, api_key, agent = _setup_agent_and_key(client)

    draft = _submit_draft(
        client,
        api_key,
        agent["id"],
        _draft_payload(
            task="Kubernetes rollout",
            problem="Pod crash loop on missing config",
            solution="Mount configmap before deployment",
            capability_tags=["kubernetes"],
        ),
    )
    _approve(client, auth["access_token"], draft["draft_id"], publish_to_network=True)

    match = client.get("/experiences/search", params={"scope": "public", "q": "configmap"})
    assert match.status_code == 200
    assert match.json()["total"] == 1

    miss = client.get("/experiences/search", params={"scope": "public", "q": "terraform"})
    assert miss.status_code == 200
    assert miss.json()["total"] == 0


def test_public_search_tag_and_tool_filters(client: TestClient):
    auth, api_key, agent = _setup_agent_and_key(client)

    matching = _submit_draft(
        client,
        api_key,
        agent["id"],
        _draft_payload(task="Tagged task", capability_tags=["python", "pytest"]),
    )
    other = _submit_draft(
        client,
        api_key,
        agent["id"],
        _draft_payload(task="Other task", capability_tags=["python"]),
    )
    _approve(client, auth["access_token"], matching["draft_id"], publish_to_network=True)
    _approve(client, auth["access_token"], other["draft_id"], publish_to_network=True)

    response = client.get(
        "/experiences/search",
        params={"scope": "public", "tags": ["python"], "tools": ["pytest"]},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["task"] == "Tagged task"
    assert body["items"][0]["capability_tags"] == ["pytest", "python"]


def test_org_search_requires_auth(client: TestClient):
    response = client.get("/experiences/search", params={"scope": "org"})
    assert response.status_code == 401


def test_org_search_returns_private_and_public(client: TestClient):
    auth, api_key, agent = _setup_agent_and_key(client)
    headers = _agent_headers(api_key, agent["id"])

    private_draft = _submit_draft(
        client,
        api_key,
        agent["id"],
        _draft_payload(task="Org private task"),
    )
    public_draft = _submit_draft(
        client,
        api_key,
        agent["id"],
        _draft_payload(task="Org public task"),
    )
    _approve(client, auth["access_token"], private_draft["draft_id"], publish_to_network=False)
    _approve(client, auth["access_token"], public_draft["draft_id"], publish_to_network=True)

    response = client.get("/experiences/search", params={"scope": "org"}, headers=headers)

    assert response.status_code == 200
    tasks = {item["task"] for item in response.json()["items"]}
    assert tasks == {"Org private task", "Org public task"}


def test_org_search_excludes_other_operators_private(client: TestClient):
    auth_a, api_key_a, agent_a = _setup_agent_and_key(client)
    headers_a = _agent_headers(api_key_a, agent_a["id"])

    private_a = _submit_draft(client, api_key_a, agent_a["id"], _draft_payload(task="Operator A private"))
    _approve(client, auth_a["access_token"], private_a["draft_id"], publish_to_network=False)

    auth_b, api_key_b, agent_b = _setup_agent_and_key(client)
    private_b = _submit_draft(client, api_key_b, agent_b["id"], _draft_payload(task="Operator B private"))
    _approve(client, auth_b["access_token"], private_b["draft_id"], publish_to_network=False)

    response = client.get("/experiences/search", params={"scope": "org"}, headers=headers_a)

    assert response.status_code == 200
    tasks = {item["task"] for item in response.json()["items"]}
    assert tasks == {"Operator A private"}


def test_org_search_records_usage(client: TestClient, db_session: Session):
    auth, api_key, agent = _setup_agent_and_key(client)
    headers = _agent_headers(api_key, agent["id"])

    draft = _submit_draft(client, api_key, agent["id"])
    _approve(client, auth["access_token"], draft["draft_id"], publish_to_network=False)

    before = db_session.query(ApiUsageEvent).count()
    response = client.get("/experiences/search", params={"scope": "org"}, headers=headers)
    after = db_session.query(ApiUsageEvent).count()

    assert response.status_code == 200
    assert after == before + 1
    event = db_session.query(ApiUsageEvent).order_by(ApiUsageEvent.created_at.desc()).first()
    assert event.event_type == ApiUsageEventType.search.value


def test_org_search_rate_limit(client: TestClient, db_session: Session, monkeypatch: pytest.MonkeyPatch):
    from agentnet_api.config import Settings

    updated = Settings(
        auth_dev_mode=True,
        jwt_secret="test-secret",
        rate_limit_agent_searches_per_hour=1,
        rate_limit_operator_searches_per_hour=100,
    )
    monkeypatch.setattr("agentnet_api.config.settings", updated)
    monkeypatch.setattr("agentnet_api.rate_limit.checker.settings", updated)

    auth, api_key, agent = _setup_agent_and_key(client)
    headers = _agent_headers(api_key, agent["id"])
    draft = _submit_draft(client, api_key, agent["id"])
    _approve(client, auth["access_token"], draft["draft_id"], publish_to_network=False)

    first = client.get("/experiences/search", params={"scope": "org"}, headers=headers)
    second = client.get("/experiences/search", params={"scope": "org"}, headers=headers)

    assert first.status_code == 200
    assert second.status_code == 429


def test_get_public_experience_without_auth(client: TestClient):
    auth, api_key, agent = _setup_agent_and_key(client)
    draft = _submit_draft(client, api_key, agent["id"])
    _approve(client, auth["access_token"], draft["draft_id"], publish_to_network=True)

    response = client.get(f"/experiences/{draft['draft_id']}")

    assert response.status_code == 200
    body = response.json()
    assert body["visibility"] == "public"
    assert body["post"]["task"] == "Deploy FastAPI to Railway"
    assert body["post"]["solution"]


def test_get_private_experience_requires_org_agent(client: TestClient):
    auth, api_key, agent = _setup_agent_and_key(client)
    draft = _submit_draft(client, api_key, agent["id"])
    _approve(client, auth["access_token"], draft["draft_id"], publish_to_network=False)

    unauth = client.get(f"/experiences/{draft['draft_id']}")
    assert unauth.status_code == 404

    authed = client.get(
        f"/experiences/{draft['draft_id']}",
        headers=_agent_headers(api_key, agent["id"]),
    )
    assert authed.status_code == 200
    assert authed.json()["visibility"] == "private"


def test_get_private_experience_forbidden_for_other_operator(client: TestClient):
    auth_a, api_key_a, agent_a = _setup_agent_and_key(client)
    draft = _submit_draft(client, api_key_a, agent_a["id"])
    _approve(client, auth_a["access_token"], draft["draft_id"], publish_to_network=False)

    _, api_key_b, agent_b = _setup_agent_and_key(client)
    response = client.get(
        f"/experiences/{draft['draft_id']}",
        headers=_agent_headers(api_key_b, agent_b["id"]),
    )
    assert response.status_code == 404


def test_get_draft_returns_not_found(client: TestClient):
    auth, api_key, agent = _setup_agent_and_key(client)
    draft = _submit_draft(client, api_key, agent["id"])

    response = client.get(
        f"/experiences/{draft['draft_id']}",
        headers=_agent_headers(api_key, agent["id"]),
    )
    assert response.status_code == 404


def test_search_pagination(client: TestClient, db_session: Session):
    auth, api_key, agent = _setup_agent_and_key(client)
    operator_id = uuid.UUID(agent["id"])
    agent_row = db_session.get(Experience, uuid.UUID(_submit_draft(client, api_key, agent["id"])["draft_id"]))
    operator_uuid = agent_row.operator_id

    for index in range(3):
        experience = Experience(
            operator_id=operator_uuid,
            agent_id=operator_id,
            status=ExperienceStatus.approved,
            visibility=ExperienceVisibility.public,
            content=_draft_payload(task=f"Paginated task {index}"),
            task=f"Paginated task {index}",
            problem=f"Problem {index}",
            solution=f"Solution {index}",
            success=True,
            approved_at=datetime.now(UTC),
            tags=resolve_capability_tags(db_session, ["python"]),
        )
        db_session.add(experience)
    db_session.flush()

    page = client.get(
        "/experiences/search",
        params={"scope": "public", "limit": 2, "offset": 1},
    )

    assert page.status_code == 200
    body = page.json()
    assert body["total"] >= 3
    assert len(body["items"]) == 2
    assert body["limit"] == 2
    assert body["offset"] == 1
