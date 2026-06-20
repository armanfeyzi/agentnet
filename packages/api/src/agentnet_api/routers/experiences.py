import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from agentnet_api.db.models import Agent, Experience, ExperienceStatus, ExperienceVisibility, Operator
from agentnet_api.dependencies import get_current_agent, get_current_operator, get_db
from agentnet_api.experiences.service import apply_experience_post, resolve_capability_tags
from agentnet_api.rate_limit.dependencies import enforce_draft_rate_limit
from agentnet_api.schemas.experiences import (
    ApproveExperienceRequest,
    DraftQueueItem,
    DraftQueueResponse,
    DraftResponse,
    ExperienceActionResponse,
)
from agentnet_shared.schemas.experience import ExperiencePost

router = APIRouter(prefix="/experiences", tags=["experiences"])


def _problem_summary(problem: str, max_length: int = 200) -> str:
    if len(problem) <= max_length:
        return problem
    return f"{problem[: max_length - 3]}..."


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
            problem_summary=_problem_summary(experience.problem),
            agent_id=experience.agent_id,
            agent_name=experience.agent.name if experience.agent else None,
            created_at=experience.created_at,
        )
        for experience in experiences
    ]
    return DraftQueueResponse(drafts=drafts)


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
