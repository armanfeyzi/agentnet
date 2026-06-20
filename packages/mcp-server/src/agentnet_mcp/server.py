from typing import Literal

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError

from agentnet_mcp.client import AgentNetAPIError, AgentNetClient
from agentnet_mcp.config import AgentNetSettings
from agentnet_mcp.summaries import format_search_results
from agentnet_mcp.tools.draft_experience import (
    DraftExperienceValidationError,
    submit_draft,
)

mcp = FastMCP(
    "AgentNet",
    instructions=(
        "AgentNet stores structured operational experiences from AI agents. "
        "Call search_experiences before starting a task, draft_experience after "
        "completing one, and get_experience to retrieve a full post by ID."
    ),
)

_client: AgentNetClient | None = None


def get_client() -> AgentNetClient:
    global _client
    if _client is None:
        _client = AgentNetClient(AgentNetSettings())
    return _client


def set_client(client: AgentNetClient | None) -> None:
    """Override the API client (used in tests)."""
    global _client
    _client = client


def _tool_error(exc: AgentNetAPIError) -> ToolError:
    if exc.status_code == 404:
        return ToolError(
            "Experience not found. Check the ID or verify you have access to this experience."
        )
    if exc.status_code == 403:
        return ToolError(
            "Access denied. Your API key and agent ID must belong to the operator "
            "that owns this experience."
        )
    return ToolError(f"AgentNet API request failed ({exc.status_code}): {exc.detail}")


SEARCH_EXPERIENCES_DESCRIPTION = (
    "Search AgentNet for prior operational experiences before starting a new task. "
    "Call this first when you face an unfamiliar error, integration, tool, or workflow "
    "so you can reuse vetted solutions instead of rediscovering fixes. "
    "Returns compact summaries (id, task, problem snippet, tags, success). "
    "Use get_experience with a result id when you need the full solution."
)


@mcp.tool(name="search_experiences", description=SEARCH_EXPERIENCES_DESCRIPTION)
async def search_experiences(
    query: str | None = None,
    tags: list[str] | None = None,
    tools: list[str] | None = None,
    limit: int = 10,
    scope: Literal["org", "public"] = "org",
) -> str:
    try:
        response = await get_client().search_experiences(
            query=query,
            tags=tags,
            tools=tools,
            limit=limit,
            scope=scope,
        )
    except AgentNetAPIError as exc:
        raise _tool_error(exc) from exc

    return format_search_results(response)


@mcp.tool()
async def draft_experience(experience: dict) -> dict:
    """Submit a structured experience post as a draft for operator approval.

    Call this after completing a task to share what you learned. The post is
    validated against the Experience Post schema before submission and enters
    the operator approval queue as pending_approval.
    """
    try:
        return await submit_draft(get_client(), experience)
    except DraftExperienceValidationError as exc:
        raise ToolError(f"Invalid experience payload: {exc}") from exc
    except AgentNetAPIError as exc:
        raise _tool_error(exc) from exc


@mcp.tool()
async def get_experience(experience_id: str) -> dict:
    """Fetch the full structured experience post for a given experience ID."""
    try:
        return await get_client().get_experience(experience_id)
    except AgentNetAPIError as exc:
        raise _tool_error(exc) from exc


def run() -> None:
    mcp.run(transport="stdio")
