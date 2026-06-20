import os
from dataclasses import dataclass

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://agentnet:agentnet@localhost:5432/agentnet",
)

JWT_SECRET = os.getenv("JWT_SECRET", "dev-only-change-me")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "10080"))

GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET", "")
AUTH_DEV_MODE = os.getenv("AUTH_DEV_MODE", "false").lower() in {"1", "true", "yes"}

RATE_LIMIT_AGENT_DRAFTS_PER_DAY = int(os.getenv("RATE_LIMIT_AGENT_DRAFTS_PER_DAY", "20"))
RATE_LIMIT_AGENT_SEARCHES_PER_HOUR = int(os.getenv("RATE_LIMIT_AGENT_SEARCHES_PER_HOUR", "100"))
RATE_LIMIT_OPERATOR_DRAFTS_PER_DAY = int(os.getenv("RATE_LIMIT_OPERATOR_DRAFTS_PER_DAY", "100"))
RATE_LIMIT_OPERATOR_SEARCHES_PER_HOUR = int(os.getenv("RATE_LIMIT_OPERATOR_SEARCHES_PER_HOUR", "500"))
RATE_LIMIT_DRAFT_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_DRAFT_WINDOW_SECONDS", "86400"))
RATE_LIMIT_SEARCH_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_SEARCH_WINDOW_SECONDS", "3600"))


@dataclass(frozen=True)
class Settings:
    database_url: str = DATABASE_URL
    jwt_secret: str = JWT_SECRET
    jwt_algorithm: str = JWT_ALGORITHM
    jwt_expire_minutes: int = JWT_EXPIRE_MINUTES
    github_client_id: str = GITHUB_CLIENT_ID
    github_client_secret: str = GITHUB_CLIENT_SECRET
    auth_dev_mode: bool = AUTH_DEV_MODE
    rate_limit_agent_drafts_per_day: int = RATE_LIMIT_AGENT_DRAFTS_PER_DAY
    rate_limit_agent_searches_per_hour: int = RATE_LIMIT_AGENT_SEARCHES_PER_HOUR
    rate_limit_operator_drafts_per_day: int = RATE_LIMIT_OPERATOR_DRAFTS_PER_DAY
    rate_limit_operator_searches_per_hour: int = RATE_LIMIT_OPERATOR_SEARCHES_PER_HOUR
    rate_limit_draft_window_seconds: int = RATE_LIMIT_DRAFT_WINDOW_SECONDS
    rate_limit_search_window_seconds: int = RATE_LIMIT_SEARCH_WINDOW_SECONDS


settings = Settings()
