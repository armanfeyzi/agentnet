FROM docker.io/library/python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml ./
COPY packages/shared/pyproject.toml packages/shared/
COPY packages/shared/src packages/shared/src
COPY packages/api/pyproject.toml packages/api/
COPY packages/api/src packages/api/src
COPY packages/api/alembic.ini packages/api/
COPY packages/api/alembic packages/api/alembic

RUN uv sync --package agentnet-api

WORKDIR /app/packages/api

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=40s --retries=5 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"

CMD ["sh", "-c", "uv run --package agentnet-api alembic upgrade head && uv run --package agentnet-api uvicorn agentnet_api.main:app --host 0.0.0.0 --port 8000"]
