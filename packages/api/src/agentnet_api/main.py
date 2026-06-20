from fastapi import FastAPI

app = FastAPI(
    title="AgentNet API",
    description="Structured knowledge network for AI agents",
    version="0.1.0",
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


def run() -> None:
    import uvicorn

    uvicorn.run("agentnet_api.main:app", host="0.0.0.0", port=8000, reload=True)
