import uuid

from fastapi.testclient import TestClient

from tests.conftest import auth_headers, register_operator


def test_create_agent(client: TestClient):
    auth = register_operator(client)
    response = client.post(
        "/agents",
        headers=auth_headers(auth["access_token"]),
        json={
            "name": "Cursor Dev Agent",
            "model_family": "claude-sonnet",
            "capability_tags": ["fastapi", "postgres"],
            "api_key_scope": "operator",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Cursor Dev Agent"
    assert body["capability_tags"] == ["fastapi", "postgres"]
    assert body["is_active"] is True
    uuid.UUID(body["id"])


def test_list_agents_returns_only_active(client: TestClient):
    auth = register_operator(client)
    headers = auth_headers(auth["access_token"])
    created = client.post(
        "/agents",
        headers=headers,
        json={"name": "Active Agent", "capability_tags": ["mcp"]},
    ).json()
    client.post(
        "/agents",
        headers=headers,
        json={"name": "Soon Inactive", "capability_tags": ["mcp"]},
    )

    client.delete(f"/agents/{created['id']}", headers=headers)

    response = client.get("/agents", headers=headers)

    assert response.status_code == 200
    names = [agent["name"] for agent in response.json()["agents"]]
    assert names == ["Soon Inactive"]


def test_get_agent_not_found_for_other_operator(client: TestClient):
    owner_auth = register_operator(client, github_id=f"owner-{uuid.uuid4().hex[:8]}")
    other_auth = register_operator(client, github_id=f"owner-{uuid.uuid4().hex[:8]}")

    created = client.post(
        "/agents",
        headers=auth_headers(owner_auth["access_token"]),
        json={"name": "Private Agent", "capability_tags": ["mcp"]},
    ).json()

    response = client.get(
        f"/agents/{created['id']}",
        headers=auth_headers(other_auth["access_token"]),
    )

    assert response.status_code == 404


def test_requires_bearer_token(client: TestClient):
    response = client.get("/agents")

    assert response.status_code == 401


def test_rejects_invalid_payload(client: TestClient):
    auth = register_operator(client)
    response = client.post(
        "/agents",
        headers=auth_headers(auth["access_token"]),
        json={"name": "", "capability_tags": ["Bad Tag"]},
    )

    assert response.status_code == 422
