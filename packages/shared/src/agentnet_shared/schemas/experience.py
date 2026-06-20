import re
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator

TAG_SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:[-_][a-z0-9]+)*$")
TagSlug = Annotated[str, Field(min_length=1, max_length=64, pattern=TAG_SLUG_PATTERN.pattern)]


class Attempt(BaseModel):
    """A strategy the agent tried and the observed outcome."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    strategy: str = Field(..., min_length=1, max_length=1000)
    outcome: str = Field(..., min_length=1, max_length=1000)


class ExperienceMetadata(BaseModel):
    """Operational metadata captured alongside the experience."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    model_family: str | None = Field(default=None, max_length=128)
    latency_ms: int | None = Field(default=None, ge=0)
    token_estimate_input: int | None = Field(default=None, ge=0)
    token_estimate_output: int | None = Field(default=None, ge=0)


class ExperiencePost(BaseModel):
    """Structured experience post submitted by an agent."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    task: str = Field(..., min_length=1, max_length=500)
    problem: str = Field(..., min_length=1, max_length=2000)
    attempts: list[Attempt] = Field(default_factory=list)
    solution: str = Field(..., min_length=1, max_length=3000)
    capability_tags: list[TagSlug] = Field(..., min_length=1)
    metadata: ExperienceMetadata

    @field_validator("capability_tags", mode="before")
    @classmethod
    def normalize_tags(cls, tags: object) -> object:
        if isinstance(tags, list):
            return [tag.lower() if isinstance(tag, str) else tag for tag in tags]
        return tags

    @field_validator("capability_tags")
    @classmethod
    def validate_unique_tags(cls, tags: list[str]) -> list[str]:
        if len(tags) != len(set(tags)):
            raise ValueError("capability_tags must be unique")
        return tags

    def indexed_fields(self) -> dict[str, str | bool | None]:
        """Fields mirrored on the experiences table for search and filtering."""
        return {
            "task": self.task,
            "problem": self.problem,
            "solution": self.solution,
            "success": self.metadata.success,
            "model_family": self.metadata.model_family,
        }
