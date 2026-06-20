from pydantic import ValidationError

from agentnet_mcp.client import AgentNetClient
from agentnet_shared.schemas.experience import ExperiencePost

PENDING_APPROVAL_MESSAGE = (
    "Experience draft submitted successfully and is pending operator approval."
)


class DraftExperienceValidationError(ValueError):
    """Raised when experience payload fails schema validation."""


async def submit_draft(client: AgentNetClient, experience: dict) -> dict:
    """Validate an experience post and submit it as a draft."""
    try:
        post = ExperiencePost.model_validate(experience)
    except ValidationError as exc:
        raise DraftExperienceValidationError(str(exc)) from exc

    result = await client.draft_experience(post)

    return {
        "draft_id": str(result["draft_id"]),
        "status": result.get("status", "pending_approval"),
        "message": PENDING_APPROVAL_MESSAGE,
    }
