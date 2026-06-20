import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://agentnet:agentnet@localhost:5432/agentnet",
)
