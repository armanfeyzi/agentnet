from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from agentnet_api.db.models import Agent, CapabilityTag, Experience, ExperienceStatus, ExperienceVisibility
from agentnet_api.dependencies import get_current_agent, get_db
from agentnet_api.rate_limit.dependencies import enforce_draft_rate_limit
from agentnet_api.schemas.experiences import DraftResponse
from agentnet_shared.schemas.experience import ExperiencePost

router = APIRouter(prefix="/experiences", tags=["experiences"])


@router.post("/draft", response_model=DraftResponse, status_code=status.HTTP_201_CREATED)
def create_draft_experience(
    payload: ExperiencePost,
    agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db),
    _: None = Depends(enforce_draft_rate_limit),
) -> DraftResponse:
    db_tags = []
    for tag_slug in payload.capability_tags:
        db_tag = db.scalar(
            select(CapabilityTag).where(CapabilityTag.slug == tag_slug)
        )
        if not db_tag:
            db_tag = CapabilityTag(slug=tag_slug)
            db.add(db_tag)
            db.flush()
        db_tags.append(db_tag)

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
