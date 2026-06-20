import uuid

from fastapi.testclient import TestClient

from tests.conftest import auth_headers, register_operator


def test_register_and_login(client: TestClient):
    github_id = f"auth-user-{uuid.uuid4().hex[:8]}"
    register_response = client.post(
        "/auth/register",
        json={
            "github_id": github_id,
            "name": "Auth User",
            "email": f"{github_id}@example.com",
        },
    )
    assert register_response.status_code == 201
    register_body = register_response.json()
    assert register_body["token_type"] == "bearer"
    assert register_body["operator"]["github_id"] == github_id

    duplicate = client.post(
        "/auth/register",
        json={
            "github_id": github_id,
            "name": "Auth User",
            "email": f"{github_id}@example.com",
        },
    )
    assert duplicate.status_code == 409

    login_response = client.post(
        "/auth/login",
        json={
            "github_id": github_id,
            "name": "Auth User Updated",
            "email": f"{github_id}@example.com",
        },
    )
    assert login_response.status_code == 200
    assert login_response.json()["operator"]["name"] == "Auth User Updated"


def test_login_requires_registration(client: TestClient):
    response = client.post(
        "/auth/login",
        json={"github_id": "missing-user", "name": "Missing User"},
    )

    assert response.status_code == 404


def test_get_operator_profile(client: TestClient):
    github_id = f"profile-user-{uuid.uuid4().hex[:8]}"
    auth = register_operator(client, github_id=github_id, email=f"{github_id}@example.com")

    response = client.get("/operators/me", headers=auth_headers(auth["access_token"]))

    assert response.status_code == 200
    body = response.json()
    assert body["email"] == f"{github_id}@example.com"
    assert body["github_id"] == github_id


def test_create_api_key(client: TestClient):
    auth = register_operator(client, github_id=f"api-key-user-{uuid.uuid4().hex[:8]}")

    response = client.post(
        "/operators/me/api-keys",
        headers=auth_headers(auth["access_token"]),
        json={"name": "Cursor MCP"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Cursor MCP"
    assert body["api_key"].startswith("op_")
    assert body["key_prefix"] == body["api_key"][:12]
