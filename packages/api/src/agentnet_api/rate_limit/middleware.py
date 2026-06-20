from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from agentnet_api.rate_limit.exceptions import RateLimitExceeded


async def rate_limit_exception_handler(_request: Request, exc: RateLimitExceeded) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content={"detail": exc.detail},
        headers={"Retry-After": str(exc.retry_after)},
    )


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Attach rate-limit handling to the ASGI stack."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        return await call_next(request)
