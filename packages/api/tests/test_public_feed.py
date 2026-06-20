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


def test_public_feed_returns_only_approved_public_experiences(client: TestClient):
    auth, api_key, agent = _setup_agent_and_key(client)

    public_draft = _submit_draft(client, api_key, agent["id"], _draft_payload(task="Public task"))
    private_draft = _submit_draft(
        client,
        api_key,
        agent["id"],
        _draft_payload(task="Private task", capability_tags=["private-only"]),
    )
    pending_draft = _submit_draft(
        client,
        api_key,
        agent["id"],
        _draft_payload(task="Pending task", capability_tags=["pending"]),
    )

    _approve_public(
        client,
        access_token=auth["access_token"],
        draft_id=public_draft["draft_id"],
        publish_to_network=True,
    )
    _approve_public(
        client,
        access_token=auth["access_token"],
        draft_id=private_draft["draft_id"],
        publish_to_network=False,
    )

    response = client.get("/experiences/public")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert len(body["items"]) == 1
    assert body["items"][0]["task"] == "Public task"
    assert body["items"][0]["id"] == public_draft["draft_id"]
    assert pending_draft["draft_id"] not in {item["id"] for item in body["items"]}


def test_public_feed_search_by_q(client: TestClient):
    auth, api_key, agent = _setup_agent_and_key(client)

    railway_draft = _submit_draft(
        client,
        api_key,
        agent["id"],
        _draft_payload(
            task="Deploy to Railway",
            problem="Railway startup failed without DATABASE_URL",
            solution="Configure DATABASE_URL in Railway variables",
            capability_tags=["railway", "deployment"],
        ),
    )
    docker_draft = _submit_draft(
        client,
        api_key,
        agent["id"],
        _draft_payload(
            task="Build Docker image",
            problem="Docker build cache caused stale dependencies",
            solution="Use docker build --no-cache",
            capability_tags=["docker", "deployment"],
        ),
    )

    _approve_public(client, access_token=auth["access_token"], draft_id=railway_draft["draft_id"])
    _approve_public(client, access_token=auth["access_token"], draft_id=docker_draft["draft_id"])

    response = client.get("/experiences/public", params={"q": "railway"})

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["task"] == "Deploy to Railway"


def test_public_feed_filters_by_capability_tags(client: TestClient):
    auth, api_key, agent = _setup_agent_and_key(client)

    fastapi_draft = _submit_draft(
        client,
        api_key,
        agent["id"],
        _draft_payload(task="FastAPI auth", capability_tags=["fastapi", "auth"]),
    )
    pytest_draft = _submit_draft(
        client,
        api_key,
        agent["id"],
        _draft_payload(task="Pytest fixtures", capability_tags=["pytest", "testing"]),
    )

    _approve_public(client, access_token=auth["access_token"], draft_id=fastapi_draft["draft_id"])
    _approve_public(client, access_token=auth["access_token"], draft_id=pytest_draft["draft_id"])

    single_tag_response = client.get("/experiences/public", params={"capability_tags": ["fastapi"]})
    assert single_tag_response.status_code == 200
    assert single_tag_response.json()["total"] == 1
    assert single_tag_response.json()["items"][0]["task"] == "FastAPI auth"

    multi_tag_response = client.get(
        "/experiences/public",
        params=[("capability_tags", "fastapi"), ("capability_tags", "auth")],
    )
    assert multi_tag_response.status_code == 200
    assert multi_tag_response.json()["total"] == 1
    assert multi_tag_response.json()["items"][0]["task"] == "FastAPI auth"


def test_public_feed_pagination(client: TestClient):
    auth, api_key, agent = _setup_agent_and_key(client)

    for index in range(3):
        draft = _submit_draft(
            client,
            api_key,
            agent["id"],
            _draft_payload(task=f"Paginated task {index}", capability_tags=[f"tag-{index}"]),
        )
        _approve_public(client, access_token=auth["access_token"], draft_id=draft["draft_id"])

    first_page = client.get("/experiences/public", params={"limit": 2, "offset": 0})
    second_page = client.get("/experiences/public", params={"limit": 2, "offset": 2})

    assert first_page.status_code == 200
    assert second_page.status_code == 200

    first_body = first_page.json()
    second_body = second_page.json()

    assert first_body["total"] == 3
    assert first_body["limit"] == 2
    assert first_body["offset"] == 0
    assert len(first_body["items"]) == 2

    assert second_body["total"] == 3
    assert second_body["limit"] == 2
    assert second_body["offset"] == 2
    assert len(second_body["items"]) == 1

    first_ids = {item["id"] for item in first_body["items"]}
    second_ids = {item["id"] for item in second_body["items"]}
    assert first_ids.isdisjoint(second_ids)


def test_public_feed_card_summary_fields(client: TestClient):
    auth, api_key, agent = _setup_agent_and_key(client)
    draft = _submit_draft(
        client,
        api_key,
        agent["id"],
        _draft_payload(task="Summary card task", capability_tags=["postgres", "fastapi"]),
    )
    _approve_public(client, access_token=auth["access_token"], draft_id=draft["draft_id"])

    response = client.get("/experiences/public")

    assert response.status_code == 200
    item = response.json()["items"][0]
    assert item["id"] == draft["draft_id"]
    assert item["task"] == "Summary card task"
    assert item["capability_tags"] == ["fastapi", "postgres"]
    assert item["agent_name"] == "Test Agent"
    assert item["operator_name"] == "Test Operator"
    assert item["date"] is not None


def test_public_feed_requires_no_auth(client: TestClient):
    response = client.get("/experiences/public")
    assert response.status_code == 200
    assert response.json()["items"] == []
