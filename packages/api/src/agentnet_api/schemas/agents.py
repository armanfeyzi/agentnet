import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from agentnet_shared.schemas import AgentRegistration


class AgentResponse(BaseModel):
    id: uuid.UUID
    name: str
    model_family: str | None
    capability_tags: list[str]
    api_key_scope: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AgentListResponse(BaseModel):
    agents: list[AgentResponse] = Field(default_factory=list)


class PublicAgentExperienceCard(BaseModel):
    id: uuid.UUID
    task: str
    capability_tags: list[str] = Field(default_factory=list)
    date: datetime


class PublicAgentProfileResponse(BaseModel):
    id: uuid.UUID
    name: str
    model_family: str | None
    capability_tags: list[str] = Field(default_factory=list)
    operator_name: str
    experiences: list[PublicAgentExperienceCard] = Field(default_factory=list)
    total_experiences: int
    limit: int
    offset: int


__all__ = [
    "AgentListResponse",
    "AgentRegistration",
    "AgentResponse",
    "PublicAgentExperienceCard",
    "PublicAgentProfileResponse",
]
