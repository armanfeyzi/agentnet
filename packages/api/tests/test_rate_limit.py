import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from agentnet_api.config import Settings
from agentnet_api.db.models import Agent, ApiUsageEvent, ApiUsageEventType, Experience, ExperienceStatus, ExperienceVisibility, Operator
from agentnet_api.rate_limit.checker import check_search_rate_limits, record_search_usage
from agentnet_api.rate_limit.exceptions import RateLimitExceeded
from tests.test_experiences import _setup_agent_and_key


def _patch_rate_limits(monkeypatch: pytest.MonkeyPatch, **overrides: int) -> Settings:
    updated = Settings(
        auth_dev_mode=True,
        jwt_secret="test-secret",
        **overrides,
    )
    monkeypatch.setattr("agentnet_api.config.settings", updated)
    monkeypatch.setattr("agentnet_api.rate_limit.checker.settings", updated)
    return updated


def test_operator_draft_rate_limit(client: TestClient, db_session: Session, monkeypatch: pytest.MonkeyPatch):
    _patch_rate_limits(
        monkeypatch,
        rate_limit_agent_drafts_per_day=50,
        rate_limit_operator_drafts_per_day=3,
    )
    _, api_key, agent = _setup_agent_and_key(client)
    agent_uuid = uuid.UUID(agent["id"])
    agent_db = db_session.get(Agent, agent_uuid)
    operator_uuid = agent_db.operator_id

    for i in range(3):
        db_session.add(
            Experience(
                operator_id=operator_uuid,
                agent_id=agent_uuid,
                status=ExperienceStatus.draft,
                visibility=ExperienceVisibility.private,
                content={},
                task=f"Operator limit task {i}",
                problem=f"Problem {i}",
                solution=f"Solution {i}",
                success=True,
            )
        )
    db_session.flush()

    response = client.post(
        "/experiences/draft",
        headers={"X-API-Key": api_key, "X-Agent-ID": agent["id"]},
        json={
            "task": "Fourth operator draft",
            "problem": "Operator quota exceeded",
            "attempts": [],
            "solution": "Wait for retry window",
            "capability_tags": ["testing"],
            "metadata": {"success": True},
        },
    )

    assert response.status_code == 429
    assert "operator per day" in response.json()["detail"]
    assert int(response.headers["Retry-After"]) > 0


def test_agent_search_rate_limit(db_session: Session, monkeypatch: pytest.MonkeyPatch):
    _patch_rate_limits(
        monkeypatch,
        rate_limit_agent_searches_per_hour=2,
        rate_limit_operator_searches_per_hour=100,
    )

    operator = Operator(name="Search Limit Operator", github_id=f"github-{uuid.uuid4().hex[:8]}")
    db_session.add(operator)
    db_session.flush()

    agent = Agent(
        operator_id=operator.id,
        name="Search Agent",
        capability_tags=[],
    )
    db_session.add(agent)
    db_session.flush()

    record_search_usage(db_session, agent_id=agent.id, operator_id=operator.id)
    record_search_usage(db_session, agent_id=agent.id, operator_id=operator.id)

    with pytest.raises(RateLimitExceeded) as exc_info:
        check_search_rate_limits(db_session, agent_id=agent.id, operator_id=operator.id)

    assert "agent per hour" in exc_info.value.detail
    assert exc_info.value.retry_after > 0


def test_operator_search_rate_limit(db_session: Session, monkeypatch: pytest.MonkeyPatch):
    _patch_rate_limits(
        monkeypatch,
        rate_limit_agent_searches_per_hour=100,
        rate_limit_operator_searches_per_hour=2,
    )

    operator = Operator(name="Operator Search Limit", github_id=f"github-{uuid.uuid4().hex[:8]}")
    db_session.add(operator)
    db_session.flush()

    agent_a = Agent(operator_id=operator.id, name="Agent A", capability_tags=[])
    agent_b = Agent(operator_id=operator.id, name="Agent B", capability_tags=[])
    db_session.add_all([agent_a, agent_b])
    db_session.flush()

    record_search_usage(db_session, agent_id=agent_a.id, operator_id=operator.id)
    record_search_usage(db_session, agent_id=agent_b.id, operator_id=operator.id)

    with pytest.raises(RateLimitExceeded) as exc_info:
        check_search_rate_limits(db_session, agent_id=agent_a.id, operator_id=operator.id)

    assert "operator per hour" in exc_info.value.detail


def test_record_search_usage_persists_event(db_session: Session):
    operator = Operator(name="Usage Operator", github_id=f"github-{uuid.uuid4().hex[:8]}")
    db_session.add(operator)
    db_session.flush()

    agent = Agent(operator_id=operator.id, name="Usage Agent", capability_tags=[])
    db_session.add(agent)
    db_session.flush()

    record_search_usage(db_session, agent_id=agent.id, operator_id=operator.id)

    count = db_session.scalar(
        select(func.count())
        .select_from(ApiUsageEvent)
        .where(ApiUsageEvent.agent_id == agent.id)
    )
    assert count == 1

    event = db_session.scalar(select(ApiUsageEvent).where(ApiUsageEvent.agent_id == agent.id))
    assert event is not None
    assert event.event_type == ApiUsageEventType.search.value
