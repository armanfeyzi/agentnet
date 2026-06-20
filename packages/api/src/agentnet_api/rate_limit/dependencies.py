from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from agentnet_api.db.models import Agent
from agentnet_api.dependencies import get_current_agent, get_optional_agent, get_db
from agentnet_api.rate_limit.checker import check_draft_rate_limits, check_search_rate_limits
from agentnet_api.rate_limit.exceptions import RateLimitExceeded


def _raise_rate_limit(exc: RateLimitExceeded) -> None:
    raise HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail=exc.detail,
        headers={"Retry-After": str(exc.retry_after)},
    ) from exc


def enforce_draft_rate_limit(
    agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db),
) -> None:
    try:
        check_draft_rate_limits(db, agent_id=agent.id, operator_id=agent.operator_id)
    except RateLimitExceeded as exc:
        _raise_rate_limit(exc)


def enforce_search_rate_limit(
    agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db),
) -> None:
    try:
        check_search_rate_limits(db, agent_id=agent.id, operator_id=agent.operator_id)
    except RateLimitExceeded as exc:
        _raise_rate_limit(exc)


def enforce_optional_search_rate_limit(
    agent: Agent | None = Depends(get_optional_agent),
    db: Session = Depends(get_db),
) -> Agent | None:
    if agent is None:
        return None
    try:
        check_search_rate_limits(db, agent_id=agent.id, operator_id=agent.operator_id)
    except RateLimitExceeded as exc:
        _raise_rate_limit(exc)
    return agent
