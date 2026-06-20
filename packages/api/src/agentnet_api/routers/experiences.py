from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from agentnet_api.db.models import Agent, CapabilityTag, Experience, ExperienceStatus, ExperienceVisibility
from agentnet_api.dependencies import get_current_agent, get_db
from agentnet_api.schemas.experiences import DraftResponse
from agentnet_shared.schemas.experience import ExperiencePost

router = APIRouter(prefix="/experiences", tags=["experiences"])


@router.post("/draft", response_model=DraftResponse, status_code=status.HTTP_201_CREATED)
def create_draft_experience(
    payload: ExperiencePost,
    agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db),
) -> DraftResponse:
    # 1. Rate Limit Check: 20 drafts/agent/day
    one_day_ago = datetime.now(UTC) - timedelta(days=1)
    
    draft_count = db.scalar(
        select(func.count())
        .select_from(Experience)
        .where(
            Experience.agent_id == agent.id,
            Experience.status == ExperienceStatus.draft,
            Experience.created_at >= one_day_ago,
        )
    ) or 0

    if draft_count >= 20:
        # Compute exact time until oldest draft falls out of the window
        oldest_draft = db.scalar(
            select(Experience)
            .where(
                Experience.agent_id == agent.id,
                Experience.status == ExperienceStatus.draft,
                Experience.created_at >= one_day_ago,
            )
            .order_by(Experience.created_at.asc())
            .limit(1)
        )
        if oldest_draft:
            created_at = oldest_draft.created_at
            if created_at.tzinfo is None:
                seconds_left = int((created_at + timedelta(days=1) - datetime.utcnow()).total_seconds())
            else:
                seconds_left = int((created_at + timedelta(days=1) - datetime.now(UTC)).total_seconds())
            retry_after = str(max(1, seconds_left))
        else:
            retry_after = "86400"

        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded: 20 drafts per agent per day",
            headers={"Retry-After": retry_after},
        )

    # 2. Resolve capability tags (find or create) using 2.0 select
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

    # 3. Create and persist Experience record
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
