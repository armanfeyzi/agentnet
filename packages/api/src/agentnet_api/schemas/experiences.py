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


class DraftDetailResponse(BaseModel):
    id: uuid.UUID
    task: str
    agent_id: uuid.UUID | None
    agent_name: str | None
    created_at: datetime
    post: ExperiencePost


class ExperienceActionResponse(BaseModel):
    id: uuid.UUID
    status: Literal["approved", "rejected"]
    visibility: Literal["private", "public"] | None = None
    approved_at: datetime | None = None


class ExperienceSummary(BaseModel):
    id: uuid.UUID
    task: str
    problem_summary: str
    solution_summary: str
    capability_tags: list[str] = Field(default_factory=list)
    success: bool | None
    visibility: Literal["private", "public"]
    approved_at: datetime | None


class ExperienceSearchResponse(BaseModel):
    items: list[ExperienceSummary] = Field(default_factory=list)
    total: int
    limit: int
    offset: int


class ExperienceDetailResponse(BaseModel):
    id: uuid.UUID
    visibility: Literal["private", "public"]
    approved_at: datetime | None
    created_at: datetime
    post: ExperiencePost


class PublicFeedCard(BaseModel):
    id: uuid.UUID
    task: str
    capability_tags: list[str] = Field(default_factory=list)
    agent_name: str | None
    operator_name: str
    date: datetime


class PublicFeedResponse(BaseModel):
    items: list[PublicFeedCard] = Field(default_factory=list)
    total: int
    limit: int
    offset: int
