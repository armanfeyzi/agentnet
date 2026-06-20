FROM docker.io/library/python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml ./
COPY packages/shared/pyproject.toml packages/shared/
COPY packages/shared/src packages/shared/src
COPY packages/api/pyproject.toml packages/api/
COPY packages/api/src packages/api/src

RUN uv sync --package agentnet-api

EXPOSE 8000

CMD ["uv", "run", "--package", "agentnet-api", "uvicorn", "agentnet_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
