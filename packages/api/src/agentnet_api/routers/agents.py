import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from agentnet_api.db.models import Agent, Operator
from agentnet_api.dependencies import get_current_operator, get_db
from agentnet_api.experiences.service import PublicAgentExperiencesQuery, query_public_agent_experiences
from agentnet_api.schemas.agents import (
    AgentListResponse,
    AgentRegistration,
    AgentResponse,
    PublicAgentExperienceCard,
    PublicAgentProfileResponse,
)

router = APIRouter(prefix="/agents", tags=["agents"])


def _get_owned_agent(
    agent_id: uuid.UUID,
    operator: Operator,
    db: Session,
    *,
    active_only: bool,
) -> Agent:
    agent = db.scalar(
        select(Agent).where(
            Agent.id == agent_id,
            Agent.operator_id == operator.id,
        )
    )
    if agent is None or (active_only and not agent.is_active):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    return agent


@router.post("", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
def create_agent(
    payload: AgentRegistration,
    operator: Operator = Depends(get_current_operator),
    db: Session = Depends(get_db),
) -> Agent:
    agent = Agent(
        operator_id=operator.id,
        name=payload.name,
        model_family=payload.model_family,
        capability_tags=payload.capability_tags,
        api_key_scope=payload.api_key_scope,
    )
    db.add(agent)
    db.flush()
    db.refresh(agent)
    return agent


@router.get("", response_model=AgentListResponse)
def list_agents(
    operator: Operator = Depends(get_current_operator),
    db: Session = Depends(get_db),
) -> AgentListResponse:
    agents = db.scalars(
        select(Agent)
        .where(Agent.operator_id == operator.id, Agent.is_active.is_(True))
        .order_by(Agent.created_at.desc())
    ).all()
    return AgentListResponse(agents=list(agents))


@router.get("/{agent_id}/public", response_model=PublicAgentProfileResponse)
def get_public_agent_profile(
    agent_id: uuid.UUID,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> PublicAgentProfileResponse:
    agent = db.scalar(
        select(Agent)
        .options(selectinload(Agent.operator))
        .where(Agent.id == agent_id, Agent.is_active.is_(True))
    )
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

    result = query_public_agent_experiences(
        db,
        PublicAgentExperiencesQuery(agent_id=agent_id, limit=limit, offset=offset),
    )

    experiences = [
        PublicAgentExperienceCard(
            id=experience.id,
            task=experience.task,
            capability_tags=sorted(tag.slug for tag in experience.tags),
            date=experience.approved_at or experience.created_at,
        )
        for experience in result.experiences
    ]

    return PublicAgentProfileResponse(
        id=agent.id,
        name=agent.name,
        model_family=agent.model_family,
        capability_tags=agent.capability_tags,
        operator_name=agent.operator.name,
        experiences=experiences,
        total_experiences=result.total,
        limit=limit,
        offset=offset,
    )


@router.get("/{agent_id}", response_model=AgentResponse)
def get_agent(
    agent_id: uuid.UUID,
    operator: Operator = Depends(get_current_operator),
    db: Session = Depends(get_db),
) -> Agent:
    return _get_owned_agent(agent_id, operator, db, active_only=True)


@router.delete("/{agent_id}", response_model=AgentResponse)
def deactivate_agent(
    agent_id: uuid.UUID,
    operator: Operator = Depends(get_current_operator),
    db: Session = Depends(get_db),
) -> Agent:
    agent = _get_owned_agent(agent_id, operator, db, active_only=True)
    agent.is_active = False
    db.flush()
    db.refresh(agent)
    return agent
