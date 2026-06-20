import uuid

from fastapi.testclient import TestClient

from tests.conftest import auth_headers
from tests.test_experience_workflow import _draft_payload, _submit_draft
from tests.test_experiences import _setup_agent_and_key


def _approve_public(
    client: TestClient,
    *,
    access_token: str,
    draft_id: str,
    publish_to_network: bool = True,
) -> None:
    response = client.patch(
        f"/experiences/{draft_id}/approve",
        headers=auth_headers(access_token),
        json={"publish_to_network": publish_to_network},
    )
    assert response.status_code == 200


def test_public_agent_profile_returns_public_fields_only(client: TestClient):
    auth, api_key, agent = _setup_agent_and_key(client)

    public_draft = _submit_draft(
        client,
        api_key,
        agent["id"],
        _draft_payload(task="Public experience", capability_tags=["fastapi", "postgres"]),
    )
    private_draft = _submit_draft(
        client,
        api_key,
        agent["id"],
        _draft_payload(task="Private experience", capability_tags=["secret"]),
    )

    _approve_public(client, access_token=auth["access_token"], draft_id=public_draft["draft_id"])
    _approve_public(
        client,
        access_token=auth["access_token"],
        draft_id=private_draft["draft_id"],
        publish_to_network=False,
    )

    response = client.get(f"/agents/{agent['id']}/public")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == agent["id"]
    assert body["name"] == "Test Agent"
    assert body["model_family"] == "claude-sonnet"
    assert body["capability_tags"] == ["python", "testing"]
    assert body["operator_name"] == "Test Operator"
    assert body["total_experiences"] == 1
    assert len(body["experiences"]) == 1
    assert body["experiences"][0]["task"] == "Public experience"
    assert body["experiences"][0]["capability_tags"] == ["fastapi", "postgres"]
    assert "api_key_scope" not in body
    assert "is_active" not in body
    assert "operator_id" not in body
    assert "email" not in body
    assert "problem" not in body["experiences"][0]
    assert "solution" not in body["experiences"][0]


def test_public_agent_profile_requires_no_auth(client: TestClient):
    auth, api_key, agent = _setup_agent_and_key(client)
    draft = _submit_draft(client, api_key, agent["id"])
    _approve_public(client, access_token=auth["access_token"], draft_id=draft["draft_id"])

    response = client.get(f"/agents/{agent['id']}/public")

    assert response.status_code == 200


def test_public_agent_profile_not_found_for_inactive_agent(client: TestClient):
    auth, _, agent = _setup_agent_and_key(client)
    headers = auth_headers(auth["access_token"])

    deactivate = client.delete(f"/agents/{agent['id']}", headers=headers)
    assert deactivate.status_code == 200

    response = client.get(f"/agents/{agent['id']}/public")

    assert response.status_code == 404


def test_public_agent_profile_not_found_for_unknown_agent(client: TestClient):
    response = client.get(f"/agents/{uuid.uuid4()}/public")

    assert response.status_code == 404


def test_public_agent_profile_pagination(client: TestClient):
    auth, api_key, agent = _setup_agent_and_key(client)

    for index in range(3):
        draft = _submit_draft(
            client,
            api_key,
            agent["id"],
            _draft_payload(task=f"Public task {index}", capability_tags=[f"tag-{index}"]),
        )
        _approve_public(client, access_token=auth["access_token"], draft_id=draft["draft_id"])

    first_page = client.get(f"/agents/{agent['id']}/public", params={"limit": 2, "offset": 0})
    second_page = client.get(f"/agents/{agent['id']}/public", params={"limit": 2, "offset": 2})

    assert first_page.status_code == 200
    assert second_page.status_code == 200

    first_body = first_page.json()
    second_body = second_page.json()

    assert first_body["total_experiences"] == 3
    assert len(first_body["experiences"]) == 2
    assert len(second_body["experiences"]) == 1
