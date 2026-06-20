from sqlalchemy import text
from fastapi import FastAPI

from agentnet_api.db.session import get_engine

app = FastAPI(
    title="AgentNet API",
    description="Structured knowledge network for AI agents",
    version="0.1.0",
)


@app.get("/health")
def health() -> dict[str, str]:
    try:
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ok", "database": "ok"}
    except Exception:
        return {"status": "ok", "database": "unavailable"}


def run() -> None:
    import uvicorn

    uvicorn.run("agentnet_api.main:app", host="0.0.0.0", port=8000, reload=True)
