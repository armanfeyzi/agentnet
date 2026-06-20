from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AgentNetSettings(BaseSettings):
    """AgentNet MCP server configuration from environment variables."""

    model_config = SettingsConfigDict(env_prefix="AGENTNET_")

    api_key: str
    agent_id: str
    api_url: str = Field(default="http://localhost:8000")

    @property
    def auth_headers(self) -> dict[str, str]:
        return {
            "X-API-Key": self.api_key,
            "X-Agent-ID": self.agent_id,
        }
