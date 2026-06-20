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


@dataclass(frozen=True)
class Settings:
    database_url: str = DATABASE_URL
    jwt_secret: str = JWT_SECRET
    jwt_algorithm: str = JWT_ALGORITHM
    jwt_expire_minutes: int = JWT_EXPIRE_MINUTES
    github_client_id: str = GITHUB_CLIENT_ID
    github_client_secret: str = GITHUB_CLIENT_SECRET
    auth_dev_mode: bool = AUTH_DEV_MODE


settings = Settings()
