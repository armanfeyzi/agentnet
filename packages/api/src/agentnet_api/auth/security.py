import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta

import jwt

from agentnet_api.config import settings


class AuthError(Exception):
    pass


def hash_api_key(api_key: str) -> str:
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()


def generate_api_key() -> tuple[str, str, str]:
    """Return full key, display prefix, and hash."""
    token = secrets.token_urlsafe(32)
    api_key = f"op_{token}"
    return api_key, api_key[:12], hash_api_key(api_key)


def create_access_token(operator_id: uuid.UUID) -> str:
    expires_at = datetime.now(UTC) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {
        "sub": str(operator_id),
        "type": "operator",
        "exp": expires_at,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> uuid.UUID:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError as exc:
        raise AuthError("Invalid access token") from exc

    if payload.get("type") != "operator":
        raise AuthError("Invalid access token")

    try:
        return uuid.UUID(payload["sub"])
    except (KeyError, ValueError) as exc:
        raise AuthError("Invalid access token") from exc
