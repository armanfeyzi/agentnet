import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from agentnet_api.config import Settings
from agentnet_api.db.session import get_engine
from agentnet_api.dependencies import get_db
from agentnet_api.main import app


def _database_available() -> bool:
    try:
        with get_engine().connect() as conn:
            conn.exec_driver_sql("SELECT 1")
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(not _database_available(), reason="PostgreSQL is not available")


@pytest.fixture(autouse=True)
def test_settings(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("AUTH_DEV_MODE", "true")
    monkeypatch.setenv("JWT_SECRET", "test-secret")
    updated = Settings(
        auth_dev_mode=True,
        jwt_secret="test-secret",
    )
    monkeypatch.setattr("agentnet_api.config.settings", updated)
    monkeypatch.setattr("agentnet_api.auth.security.settings", updated)
    monkeypatch.setattr("agentnet_api.auth.github.settings", updated)
    monkeypatch.setattr("agentnet_api.rate_limit.checker.settings", updated)
    yield


@pytest.fixture
def db_session() -> Session:
    session = Session(bind=get_engine(), autoflush=False, autocommit=False)
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def client(db_session: Session) -> TestClient:
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def auth_headers(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


def register_operator(
    client: TestClient,
    *,
    github_id: str | None = None,
    name: str = "Test Operator",
    email: str | None = None,
) -> dict:
    suffix = uuid.uuid4().hex[:8]
    response = client.post(
        "/auth/register",
        json={
            "github_id": github_id or f"github-{suffix}",
            "name": name,
            "email": email or f"operator-{suffix}@example.com",
        },
    )
    assert response.status_code == 201
    return response.json()
