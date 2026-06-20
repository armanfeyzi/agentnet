import uuid
from dataclasses import dataclass
from typing import Literal

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from agentnet_api.db.models import (
    Agent,
    CapabilityTag,
    Experience,
    ExperienceStatus,
    ExperienceVisibility,
)
from agentnet_shared.schemas.experience import ExperiencePost

SearchScope = Literal["org", "public"]


@dataclass(frozen=True)
class ExperienceSearchQuery:
    scope: SearchScope
    operator_id: uuid.UUID | None = None
    q: str | None = None
    tags: tuple[str, ...] = ()
    tools: tuple[str, ...] = ()
    limit: int = 20
    offset: int = 0


@dataclass(frozen=True)
class ExperienceSearchResult:
    experiences: list[Experience]
    total: int


@dataclass(frozen=True)
class PublicAgentExperiencesQuery:
    agent_id: uuid.UUID
    limit: int = 20
    offset: int = 0


@dataclass(frozen=True)
class PublicAgentExperiencesResult:
    experiences: list[Experience]
    total: int


def query_public_agent_experiences(
    db: Session,
    query: PublicAgentExperiencesQuery,
) -> PublicAgentExperiencesResult:
    filters = [
        Experience.agent_id == query.agent_id,
        Experience.status == ExperienceStatus.approved,
        Experience.visibility == ExperienceVisibility.public,
    ]

    total = db.scalar(select(func.count()).select_from(Experience).where(*filters)) or 0

    experiences = db.scalars(
        select(Experience)
        .options(selectinload(Experience.tags))
        .where(*filters)
        .order_by(Experience.approved_at.desc(), Experience.created_at.desc())
        .limit(query.limit)
        .offset(query.offset)
    ).all()

    return PublicAgentExperiencesResult(experiences=list(experiences), total=total)


def _text_summary(text: str, max_length: int = 200) -> str:
    if len(text) <= max_length:
        return text
    return f"{text[: max_length - 3]}..."


def _search_filters(
    *,
    scope: SearchScope,
    operator_id: uuid.UUID | None,
    q: str | None,
    tag_slugs: tuple[str, ...],
) -> list:
    filters: list = [Experience.status == ExperienceStatus.approved]

    if scope == "public":
        filters.append(Experience.visibility == ExperienceVisibility.public)
    else:
        if operator_id is None:
            raise ValueError("operator_id is required for org scope")
        filters.append(Experience.operator_id == operator_id)

    if q:
        pattern = f"%{q.strip()}%"
        filters.append(
            or_(
                Experience.task.ilike(pattern),
                Experience.problem.ilike(pattern),
                Experience.solution.ilike(pattern),
            )
        )

    for tag_slug in tag_slugs:
        filters.append(Experience.tags.any(CapabilityTag.slug == tag_slug))

    return filters


def query_experiences(db: Session, query: ExperienceSearchQuery) -> ExperienceSearchResult:
    normalized_tags = tuple(sorted({tag.lower() for tag in (*query.tags, *query.tools)}))
    filters = _search_filters(
        scope=query.scope,
        operator_id=query.operator_id,
        q=query.q,
        tag_slugs=normalized_tags,
    )

    total = db.scalar(select(func.count()).select_from(Experience).where(*filters)) or 0

    experiences = db.scalars(
        select(Experience)
        .options(
            selectinload(Experience.tags),
            selectinload(Experience.agent).selectinload(Agent.operator),
        )
        .where(*filters)
        .order_by(Experience.approved_at.desc(), Experience.created_at.desc())
        .limit(query.limit)
        .offset(query.offset)
    ).all()

    return ExperienceSearchResult(experiences=list(experiences), total=total)


def can_access_experience(experience: Experience, agent: Agent | None) -> bool:
    if experience.status != ExperienceStatus.approved:
        return False
    if experience.visibility == ExperienceVisibility.public:
        return True
    return agent is not None and experience.operator_id == agent.operator_id


def get_accessible_experience(
    db: Session,
    experience_id: uuid.UUID,
    agent: Agent | None,
) -> Experience | None:
    experience = db.scalar(
        select(Experience)
        .options(selectinload(Experience.tags))
        .where(Experience.id == experience_id)
    )
    if experience is None or not can_access_experience(experience, agent):
        return None
    return experience


def text_summary(text: str, max_length: int = 200) -> str:
    return _text_summary(text, max_length)


def resolve_capability_tags(db: Session, tag_slugs: list[str]) -> list[CapabilityTag]:
    db_tags: list[CapabilityTag] = []
    for tag_slug in tag_slugs:
        db_tag = db.scalar(select(CapabilityTag).where(CapabilityTag.slug == tag_slug))
        if not db_tag:
            db_tag = CapabilityTag(slug=tag_slug)
            db.add(db_tag)
            db.flush()
        db_tags.append(db_tag)
    return db_tags


def apply_experience_post(experience: Experience, post: ExperiencePost, db: Session) -> None:
    experience.content = post.model_dump()
    for field, value in post.indexed_fields().items():
        setattr(experience, field, value)
    experience.tags = resolve_capability_tags(db, post.capability_tags)
