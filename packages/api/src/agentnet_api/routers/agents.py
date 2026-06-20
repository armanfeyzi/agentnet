import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from agentnet_api.db.models import Agent, Operator
from agentnet_api.dependencies import get_current_operator, get_db
from agentnet_api.schemas.agents import AgentListResponse, AgentRegistration, AgentResponse

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
