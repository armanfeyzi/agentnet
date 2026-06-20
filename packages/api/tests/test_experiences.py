import uuid
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from agentnet_api.auth.security import hash_api_key
from agentnet_api.db.models import Agent, Experience, ExperienceStatus, ExperienceVisibility, OperatorApiKey
from tests.conftest import auth_headers, register_operator


def _setup_agent_and_key(client: TestClient) -> tuple[dict, str, dict]:
    # 1. Register operator
    auth = register_operator(client)
    headers = auth_headers(auth["access_token"])

    # 2. Generate API Key
    api_key_resp = client.post(
        "/operators/me/api-keys",
        headers=headers,
        json={"name": "Test Key"},
    )
    assert api_key_resp.status_code == 201
    api_key = api_key_resp.json()["api_key"]

    # 3. Create Agent
    agent_resp = client.post(
        "/agents",
        headers=headers,
        json={
            "name": "Test Agent",
            "model_family": "claude-sonnet",
            "capability_tags": ["python", "testing"],
        },
    )
    assert agent_resp.status_code == 201
    agent = agent_resp.json()

    return auth, api_key, agent


def test_submit_draft_success_x_api_key(client: TestClient, db_session: Session):
    _, api_key, agent = _setup_agent_and_key(client)

    payload = {
        "task": "Test draft submission",
        "problem": "Struggled with draft setup",
        "attempts": [
            {"strategy": "Try manual header authentication", "outcome": "Worked perfectly"}
        ],
        "solution": "Use custom X-API-Key and X-Agent-ID headers",
        "capability_tags": ["FASTAPI", "postgres"],
        "metadata": {
            "success": True,
            "model_family": "claude-sonnet",
            "latency_ms": 150,
            "token_estimate_input": 100,
            "token_estimate_output": 50,
        },
    }

    headers = {
        "X-API-Key": api_key,
        "X-Agent-ID": agent["id"],
    }

    response = client.post(
        "/experiences/draft",
        headers=headers,
        json=payload,
    )

    assert response.status_code == 201
    body = response.json()
    assert "draft_id" in body
    assert body["status"] == "pending_approval"

    # Verify database state
    draft_id = uuid.UUID(body["draft_id"])
    exp = db_session.get(Experience, draft_id)
    assert exp is not None
    assert exp.status == ExperienceStatus.draft
    assert exp.visibility == ExperienceVisibility.private
    assert exp.task == "Test draft submission"
    assert exp.success is True
    assert exp.model_family == "claude-sonnet"
    assert len(exp.tags) == 2
    # Slugs should be lowercase
    slugs = [tag.slug for tag in exp.tags]
    assert "fastapi" in slugs
    assert "postgres" in slugs


def test_submit_draft_success_bearer(client: TestClient):
    _, api_key, agent = _setup_agent_and_key(client)

    payload = {
        "task": "Test bearer authorization",
        "problem": "Testing standard bearer header",
        "attempts": [],
        "solution": "Bearer scheme extraction works",
        "capability_tags": ["pytest"],
        "metadata": {"success": True},
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "X-Agent-ID": agent["id"],
    }

    response = client.post(
        "/experiences/draft",
        headers=headers,
        json=payload,
    )

    assert response.status_code == 201
    assert response.json()["status"] == "pending_approval"


def test_submit_draft_unauthorized_key(client: TestClient):
    _, _, agent = _setup_agent_and_key(client)

    payload = {
        "task": "Test auth failure",
        "problem": "Bad key",
        "attempts": [],
        "solution": "Failure",
        "capability_tags": ["test"],
        "metadata": {"success": True},
    }

    # Missing API Key
    resp = client.post(
        "/experiences/draft",
        headers={"X-Agent-ID": agent["id"]},
        json=payload,
    )
    assert resp.status_code == 401

    # Invalid API Key
    resp = client.post(
        "/experiences/draft",
        headers={"X-API-Key": "op_invalid_key", "X-Agent-ID": agent["id"]},
        json=payload,
    )
    assert resp.status_code == 401


def test_submit_draft_unauthorized_agent(client: TestClient):
    _, api_key, _ = _setup_agent_and_key(client)

    payload = {
        "task": "Test auth failure",
        "problem": "Bad agent",
        "attempts": [],
        "solution": "Failure",
        "capability_tags": ["test"],
        "metadata": {"success": True},
    }

    # Missing Agent ID
    resp = client.post(
        "/experiences/draft",
        headers={"X-API-Key": api_key},
        json=payload,
    )
    assert resp.status_code == 401

    # Invalid Agent ID format
    resp = client.post(
        "/experiences/draft",
        headers={"X-API-Key": api_key, "X-Agent-ID": "not-a-uuid"},
        json=payload,
    )
    assert resp.status_code == 400

    # Agent ID not found in database
    random_id = str(uuid.uuid4())
    resp = client.post(
        "/experiences/draft",
        headers={"X-API-Key": api_key, "X-Agent-ID": random_id},
        json=payload,
    )
    assert resp.status_code == 401


def test_submit_draft_forbidden_agent(client: TestClient):
    _, api_key, _ = _setup_agent_and_key(client)

    # Setup a second operator and their agent
    other_github_id = f"other-operator-{uuid.uuid4().hex[:8]}"
    other_auth = register_operator(client, github_id=other_github_id)
    other_headers = auth_headers(other_auth["access_token"])
    other_agent_resp = client.post(
        "/agents",
        headers=other_headers,
        json={"name": "Other Agent", "capability_tags": []},
    )
    assert other_agent_resp.status_code == 201
    other_agent_id = other_agent_resp.json()["id"]

    payload = {
        "task": "Test cross-operator draft post",
        "problem": "Agent belongs to Operator B but Operator A key is used",
        "attempts": [],
        "solution": "Must return 403 Forbidden",
        "capability_tags": ["security"],
        "metadata": {"success": False},
    }

    # Use Operator A's api_key but Operator B's agent ID
    headers = {
        "X-API-Key": api_key,
        "X-Agent-ID": other_agent_id,
    }

    response = client.post(
        "/experiences/draft",
        headers=headers,
        json=payload,
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Forbidden"


def test_submit_draft_inactive_agent(client: TestClient, db_session: Session):
    _, api_key, agent = _setup_agent_and_key(client)

    # Deactivate the agent directly in DB
    agent_db = db_session.get(Agent, uuid.UUID(agent["id"]))
    agent_db.is_active = False
    db_session.add(agent_db)
    db_session.flush()

    payload = {
        "task": "Test inactive agent draft post",
        "problem": "Agent is inactive",
        "attempts": [],
        "solution": "Must return 401 Unauthorized",
        "capability_tags": ["inactive"],
        "metadata": {"success": True},
    }

    headers = {
        "X-API-Key": api_key,
        "X-Agent-ID": agent["id"],
    }

    response = client.post(
        "/experiences/draft",
        headers=headers,
        json=payload,
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Agent is inactive"


def test_submit_draft_revoked_api_key(client: TestClient, db_session: Session):
    _, api_key, agent = _setup_agent_and_key(client)

    # Find and revoke the api key directly in DB using SQLAlchemy 2.0 select
    key_hash = hash_api_key(api_key)
    api_key_db = db_session.scalar(
        select(OperatorApiKey).where(OperatorApiKey.key_hash == key_hash)
    )
    assert api_key_db is not None
    api_key_db.revoked_at = datetime.now(UTC)
    db_session.add(api_key_db)
    db_session.flush()

    payload = {
        "task": "Test revoked key draft post",
        "problem": "API key is revoked",
        "attempts": [],
        "solution": "Must return 401 Unauthorized",
        "capability_tags": ["security"],
        "metadata": {"success": True},
    }

    headers = {
        "X-API-Key": api_key,
        "X-Agent-ID": agent["id"],
    }

    response = client.post(
        "/experiences/draft",
        headers=headers,
        json=payload,
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid API key"


def test_submit_draft_validation_error(client: TestClient):
    _, api_key, agent = _setup_agent_and_key(client)

    # Empty task and empty capability tags (which violates shared schemas)
    payload = {
        "task": "",
        "problem": "Missing task name",
        "attempts": [],
        "solution": "Task must be at least 1 character",
        "capability_tags": [],
        "metadata": {"success": True},
    }

    headers = {
        "X-API-Key": api_key,
        "X-Agent-ID": agent["id"],
    }

    response = client.post(
        "/experiences/draft",
        headers=headers,
        json=payload,
    )
    assert response.status_code == 422


def test_submit_draft_rate_limiting(client: TestClient, db_session: Session):
    _, api_key, agent = _setup_agent_and_key(client)
    agent_uuid = uuid.UUID(agent["id"])
    agent_db = db_session.get(Agent, agent_uuid)
    operator_uuid = agent_db.operator_id

    # Programmatically create 20 drafts for the agent in the database
    for i in range(20):
        exp = Experience(
            operator_id=operator_uuid,
            agent_id=agent_uuid,
            status=ExperienceStatus.draft,
            visibility=ExperienceVisibility.private,
            content={},
            task=f"Task {i}",
            problem=f"Problem {i}",
            solution=f"Solution {i}",
            success=True,
        )
        db_session.add(exp)
    db_session.flush()

    # Now attempt to submit the 21st draft via API
    payload = {
        "task": "21st submission task",
        "problem": "Exceeds daily rate limit",
        "attempts": [],
        "solution": "Wait for 24 hours",
        "capability_tags": ["testing"],
        "metadata": {"success": True},
    }

    headers = {
        "X-API-Key": api_key,
        "X-Agent-ID": agent["id"],
    }

    response = client.post(
        "/experiences/draft",
        headers=headers,
        json=payload,
    )

    assert response.status_code == 429
    assert "Rate limit exceeded" in response.json()["detail"]
    
    retry_after = response.headers.get("Retry-After")
    assert retry_after is not None
    assert int(retry_after) > 0
