from sqlalchemy import text
from fastapi import FastAPI

from agentnet_api.db.session import get_engine
from agentnet_api.routers.agents import router as agents_router
from agentnet_api.routers.auth import router as auth_router
from agentnet_api.routers.operators import router as operators_router

app = FastAPI(
    title="AgentNet API",
    description="Structured knowledge network for AI agents",
    version="0.1.0",
)

app.include_router(auth_router)
app.include_router(operators_router)
app.include_router(agents_router)


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
