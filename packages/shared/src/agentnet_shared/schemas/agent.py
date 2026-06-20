from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from agentnet_shared.schemas.experience import TagSlug


class AgentRegistration(BaseModel):
    """Payload for registering an agent under an operator."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str = Field(..., min_length=1, max_length=255)
    model_family: str | None = Field(default=None, max_length=128)
    capability_tags: list[TagSlug] = Field(default_factory=list)
    api_key_scope: Literal["operator"] = "operator"

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
