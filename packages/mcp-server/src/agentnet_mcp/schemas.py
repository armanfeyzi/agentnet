from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ExperienceSummary(BaseModel):
    """Compact experience summary returned by search."""

    model_config = ConfigDict(extra="ignore")

    id: str
    task: str
    problem_summary: str
    capability_tags: list[str] = Field(default_factory=list)
    success: bool | None = None
    visibility: Literal["private", "public"] | None = None


class SearchExperiencesResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    results: list[ExperienceSummary] = Field(default_factory=list)
    total: int | None = None
