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


__all__ = ["AgentListResponse", "AgentRegistration", "AgentResponse"]
