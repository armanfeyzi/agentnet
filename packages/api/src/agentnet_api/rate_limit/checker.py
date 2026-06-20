from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from agentnet_api.config import settings
from agentnet_api.db.models import ApiUsageEvent, ApiUsageEventType, Experience, ExperienceStatus
from agentnet_api.rate_limit.exceptions import RateLimitExceeded


def _window_start(window_seconds: int) -> datetime:
    return datetime.now(UTC) - timedelta(seconds=window_seconds)


def _retry_after_seconds(oldest_at: datetime | None, window_seconds: int) -> int:
    if oldest_at is None:
        return window_seconds

    if oldest_at.tzinfo is None:
        oldest_at = oldest_at.replace(tzinfo=UTC)

    expires_at = oldest_at + timedelta(seconds=window_seconds)
    return max(1, int((expires_at - datetime.now(UTC)).total_seconds()))


def _count_agent_drafts(db: Session, agent_id: UUID, since: datetime) -> int:
    return (
        db.scalar(
            select(func.count())
            .select_from(Experience)
            .where(
                Experience.agent_id == agent_id,
                Experience.status == ExperienceStatus.draft,
                Experience.created_at >= since,
            )
        )
        or 0
    )


def _oldest_agent_draft_at(db: Session, agent_id: UUID, since: datetime) -> datetime | None:
    return db.scalar(
        select(Experience.created_at)
        .where(
            Experience.agent_id == agent_id,
            Experience.status == ExperienceStatus.draft,
            Experience.created_at >= since,
        )
        .order_by(Experience.created_at.asc())
        .limit(1)
    )


def _count_operator_drafts(db: Session, operator_id: UUID, since: datetime) -> int:
    return (
        db.scalar(
            select(func.count())
            .select_from(Experience)
            .where(
                Experience.operator_id == operator_id,
                Experience.status == ExperienceStatus.draft,
                Experience.created_at >= since,
            )
        )
        or 0
    )


def _oldest_operator_draft_at(db: Session, operator_id: UUID, since: datetime) -> datetime | None:
    return db.scalar(
        select(Experience.created_at)
        .where(
            Experience.operator_id == operator_id,
            Experience.status == ExperienceStatus.draft,
            Experience.created_at >= since,
        )
        .order_by(Experience.created_at.asc())
        .limit(1)
    )


def _count_agent_searches(db: Session, agent_id: UUID, since: datetime) -> int:
    return (
        db.scalar(
            select(func.count())
            .select_from(ApiUsageEvent)
            .where(
                ApiUsageEvent.agent_id == agent_id,
                ApiUsageEvent.event_type == ApiUsageEventType.search.value,
                ApiUsageEvent.created_at >= since,
            )
        )
        or 0
    )


def _oldest_agent_search_at(db: Session, agent_id: UUID, since: datetime) -> datetime | None:
    return db.scalar(
        select(ApiUsageEvent.created_at)
        .where(
            ApiUsageEvent.agent_id == agent_id,
            ApiUsageEvent.event_type == ApiUsageEventType.search.value,
            ApiUsageEvent.created_at >= since,
        )
        .order_by(ApiUsageEvent.created_at.asc())
        .limit(1)
    )


def _count_operator_searches(db: Session, operator_id: UUID, since: datetime) -> int:
    return (
        db.scalar(
            select(func.count())
            .select_from(ApiUsageEvent)
            .where(
                ApiUsageEvent.operator_id == operator_id,
                ApiUsageEvent.event_type == ApiUsageEventType.search.value,
                ApiUsageEvent.created_at >= since,
            )
        )
        or 0
    )


def _oldest_operator_search_at(db: Session, operator_id: UUID, since: datetime) -> datetime | None:
    return db.scalar(
        select(ApiUsageEvent.created_at)
        .where(
            ApiUsageEvent.operator_id == operator_id,
            ApiUsageEvent.event_type == ApiUsageEventType.search.value,
            ApiUsageEvent.created_at >= since,
        )
        .order_by(ApiUsageEvent.created_at.asc())
        .limit(1)
    )


def check_draft_rate_limits(db: Session, *, agent_id: UUID, operator_id: UUID) -> None:
    since = _window_start(settings.rate_limit_draft_window_seconds)

    agent_count = _count_agent_drafts(db, agent_id, since)
    if agent_count >= settings.rate_limit_agent_drafts_per_day:
        raise RateLimitExceeded(
            detail=(
                f"Rate limit exceeded: {settings.rate_limit_agent_drafts_per_day} "
                "drafts per agent per day"
            ),
            retry_after=_retry_after_seconds(
                _oldest_agent_draft_at(db, agent_id, since),
                settings.rate_limit_draft_window_seconds,
            ),
        )

    operator_count = _count_operator_drafts(db, operator_id, since)
    if operator_count >= settings.rate_limit_operator_drafts_per_day:
        raise RateLimitExceeded(
            detail=(
                f"Rate limit exceeded: {settings.rate_limit_operator_drafts_per_day} "
                "drafts per operator per day"
            ),
            retry_after=_retry_after_seconds(
                _oldest_operator_draft_at(db, operator_id, since),
                settings.rate_limit_draft_window_seconds,
            ),
        )


def check_search_rate_limits(db: Session, *, agent_id: UUID, operator_id: UUID) -> None:
    since = _window_start(settings.rate_limit_search_window_seconds)

    agent_count = _count_agent_searches(db, agent_id, since)
    if agent_count >= settings.rate_limit_agent_searches_per_hour:
        raise RateLimitExceeded(
            detail=(
                f"Rate limit exceeded: {settings.rate_limit_agent_searches_per_hour} "
                "searches per agent per hour"
            ),
            retry_after=_retry_after_seconds(
                _oldest_agent_search_at(db, agent_id, since),
                settings.rate_limit_search_window_seconds,
            ),
        )

    operator_count = _count_operator_searches(db, operator_id, since)
    if operator_count >= settings.rate_limit_operator_searches_per_hour:
        raise RateLimitExceeded(
            detail=(
                f"Rate limit exceeded: {settings.rate_limit_operator_searches_per_hour} "
                "searches per operator per hour"
            ),
            retry_after=_retry_after_seconds(
                _oldest_operator_search_at(db, operator_id, since),
                settings.rate_limit_search_window_seconds,
            ),
        )


def record_search_usage(db: Session, *, agent_id: UUID, operator_id: UUID) -> None:
    db.add(
        ApiUsageEvent(
            agent_id=agent_id,
            operator_id=operator_id,
            event_type=ApiUsageEventType.search.value,
        )
    )
    db.flush()
