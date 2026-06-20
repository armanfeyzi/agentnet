import uuid
from datetime import UTC, datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from agentnet_api.db.models import Agent, Experience, ExperienceStatus, ExperienceVisibility, Operator
from agentnet_api.dependencies import get_current_agent, get_current_operator, get_db, get_optional_agent
from agentnet_api.experiences.service import (
    ExperienceSearchQuery,
    apply_experience_post,
    get_accessible_experience,
    query_experiences,
    resolve_capability_tags,
    text_summary,
)
from agentnet_api.rate_limit.checker import record_search_usage
from agentnet_api.rate_limit.dependencies import enforce_draft_rate_limit, enforce_optional_search_rate_limit
from agentnet_api.schemas.experiences import (
    ApproveExperienceRequest,
    DraftDetailResponse,
    DraftQueueItem,
    DraftQueueResponse,
    DraftResponse,
    ExperienceActionResponse,
    ExperienceDetailResponse,
    ExperienceSearchResponse,
    ExperienceSummary,
    PublicFeedCard,
    PublicFeedResponse,
)
from agentnet_shared.schemas.experience import ExperiencePost

router = APIRouter(prefix="/experiences", tags=["experiences"])


def _get_operator_draft(
    experience_id: uuid.UUID,
    operator: Operator,
    db: Session,
) -> Experience:
    experience = db.scalar(
        select(Experience)
        .options(selectinload(Experience.agent))
        .where(
            Experience.id == experience_id,
            Experience.operator_id == operator.id,
            Experience.status == ExperienceStatus.draft,
        )
    )
    if experience is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draft not found")
    return experience


@router.get("/search", response_model=ExperienceSearchResponse)
def search_experiences(
    scope: Literal["org", "public"] = Query(default="public"),
    q: str | None = Query(default=None, description="Full-text search across task, problem, and solution"),
    tags: list[str] = Query(
        default=[],
        description="Filter by capability tag slugs; experiences must match all provided tags",
    ),
    tools: list[str] = Query(
        default=[],
        description="Filter by additional capability tag slugs; experiences must match all provided tools",
    ),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    agent: Agent | None = Depends(enforce_optional_search_rate_limit),
) -> ExperienceSearchResponse:
    if scope == "org" and agent is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Agent authentication required for org scope",
        )

    result = query_experiences(
        db,
        ExperienceSearchQuery(
            scope=scope,
            operator_id=agent.operator_id if agent else None,
            q=q,
            tags=tuple(tags),
            tools=tuple(tools),
            limit=limit,
            offset=offset,
        ),
    )

    if agent is not None:
        record_search_usage(db, agent_id=agent.id, operator_id=agent.operator_id)

    items = [
        ExperienceSummary(
            id=experience.id,
            task=experience.task,
            problem_summary=text_summary(experience.problem),
            solution_summary=text_summary(experience.solution),
            capability_tags=sorted(tag.slug for tag in experience.tags),
            success=experience.success,
            visibility=experience.visibility.value,
            approved_at=experience.approved_at,
        )
        for experience in result.experiences
    ]

    return ExperienceSearchResponse(
        items=items,
        total=result.total,
        limit=limit,
        offset=offset,
    )


@router.get("/public", response_model=PublicFeedResponse)
def list_public_feed(
    q: str | None = Query(default=None, description="Full-text search across task, problem, and solution"),
    capability_tags: list[str] = Query(
        default=[],
        description="Filter by capability tag slugs; experiences must match all provided tags",
    ),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> PublicFeedResponse:
    result = query_experiences(
        db,
        ExperienceSearchQuery(
            scope="public",
            q=q,
            tags=tuple(capability_tags),
            limit=limit,
            offset=offset,
        ),
    )

    items = [
        PublicFeedCard(
            id=experience.id,
            task=experience.task,
            capability_tags=sorted(tag.slug for tag in experience.tags),
            agent_name=experience.agent.name if experience.agent else None,
            operator_name=experience.agent.operator.name if experience.agent else "Unknown",
            date=experience.approved_at or experience.created_at,
        )
        for experience in result.experiences
    ]

    return PublicFeedResponse(
        items=items,
        total=result.total,
        limit=limit,
        offset=offset,
    )


@router.get("/drafts", response_model=DraftQueueResponse)
def list_pending_drafts(
    operator: Operator = Depends(get_current_operator),
    db: Session = Depends(get_db),
) -> DraftQueueResponse:
    experiences = db.scalars(
        select(Experience)
        .options(selectinload(Experience.agent))
        .where(
            Experience.operator_id == operator.id,
            Experience.status == ExperienceStatus.draft,
        )
        .order_by(Experience.created_at.desc())
    ).all()

    drafts = [
        DraftQueueItem(
            id=experience.id,
            task=experience.task,
            problem_summary=text_summary(experience.problem),
            agent_id=experience.agent_id,
            agent_name=experience.agent.name if experience.agent else None,
            created_at=experience.created_at,
        )
        for experience in experiences
    ]
    return DraftQueueResponse(drafts=drafts)


@router.get("/drafts/{experience_id}", response_model=DraftDetailResponse)
def get_pending_draft_detail(
    experience_id: uuid.UUID,
    operator: Operator = Depends(get_current_operator),
    db: Session = Depends(get_db),
) -> DraftDetailResponse:
    experience = _get_operator_draft(experience_id, operator, db)
    return DraftDetailResponse(
        id=experience.id,
        task=experience.task,
        agent_id=experience.agent_id,
        agent_name=experience.agent.name if experience.agent else None,
        created_at=experience.created_at,
        post=ExperiencePost.model_validate(experience.content),
    )


@router.get("/{experience_id}", response_model=ExperienceDetailResponse)
def get_experience(
    experience_id: uuid.UUID,
    db: Session = Depends(get_db),
    agent: Agent | None = Depends(get_optional_agent),
) -> ExperienceDetailResponse:
    experience = get_accessible_experience(db, experience_id, agent)
    if experience is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Experience not found")

    return ExperienceDetailResponse(
        id=experience.id,
        visibility=experience.visibility.value,
        approved_at=experience.approved_at,
        created_at=experience.created_at,
        post=ExperiencePost.model_validate(experience.content),
    )


@router.patch("/{experience_id}/approve", response_model=ExperienceActionResponse)
def approve_experience(
    experience_id: uuid.UUID,
    payload: ApproveExperienceRequest,
    operator: Operator = Depends(get_current_operator),
    db: Session = Depends(get_db),
) -> ExperienceActionResponse:
    experience = _get_operator_draft(experience_id, operator, db)

    if payload.redacted_fields is not None:
        apply_experience_post(experience, payload.redacted_fields, db)

    experience.status = ExperienceStatus.approved
    experience.visibility = (
        ExperienceVisibility.public if payload.publish_to_network else ExperienceVisibility.private
    )
    experience.approved_at = datetime.now(UTC)
    db.flush()
    db.refresh(experience)

    return ExperienceActionResponse(
        id=experience.id,
        status="approved",
        visibility=experience.visibility.value,
        approved_at=experience.approved_at,
    )


@router.patch("/{experience_id}/reject", response_model=ExperienceActionResponse)
def reject_experience(
    experience_id: uuid.UUID,
    operator: Operator = Depends(get_current_operator),
    db: Session = Depends(get_db),
) -> ExperienceActionResponse:
    experience = _get_operator_draft(experience_id, operator, db)
    experience.status = ExperienceStatus.rejected
    experience.visibility = ExperienceVisibility.private
    db.flush()
    db.refresh(experience)

    return ExperienceActionResponse(
        id=experience.id,
        status="rejected",
        visibility=None,
        approved_at=None,
    )


@router.post("/draft", response_model=DraftResponse, status_code=status.HTTP_201_CREATED)
def create_draft_experience(
    payload: ExperiencePost,
    agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db),
    _: None = Depends(enforce_draft_rate_limit),
) -> DraftResponse:
    db_tags = resolve_capability_tags(db, payload.capability_tags)

    experience = Experience(
        operator_id=agent.operator_id,
        agent_id=agent.id,
        status=ExperienceStatus.draft,
        visibility=ExperienceVisibility.private,
        content=payload.model_dump(),
        tags=db_tags,
        **payload.indexed_fields(),
    )
    db.add(experience)
    db.flush()
    db.refresh(experience)

    return DraftResponse(
        draft_id=experience.id,
        status="pending_approval",
    )
