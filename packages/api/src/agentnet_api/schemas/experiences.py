import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from agentnet_shared.schemas.experience import ExperiencePost


class DraftResponse(BaseModel):
    draft_id: uuid.UUID
    status: Literal["pending_approval"]


class ApproveExperienceRequest(BaseModel):
    publish_to_network: bool = False
    redacted_fields: ExperiencePost | None = None


class DraftQueueItem(BaseModel):
    id: uuid.UUID
    task: str
    problem_summary: str
    agent_id: uuid.UUID | None
    agent_name: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DraftQueueResponse(BaseModel):
    drafts: list[DraftQueueItem] = Field(default_factory=list)


class ExperienceActionResponse(BaseModel):
    id: uuid.UUID
    status: Literal["approved", "rejected"]
    visibility: Literal["private", "public"] | None = None
    approved_at: datetime | None = None
