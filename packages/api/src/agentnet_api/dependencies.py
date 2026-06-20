import uuid
from collections.abc import Generator
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from agentnet_api.auth.security import AuthError, decode_access_token, hash_api_key
from agentnet_api.db.models import Agent, Operator, OperatorApiKey
from agentnet_api.db.session import get_session_factory

bearer_scheme = HTTPBearer(auto_error=False)


def get_db() -> Generator[Session, None, None]:
    session = get_session_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_current_operator(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: Session = Depends(get_db),
) -> Operator:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        operator_id = decode_access_token(credentials.credentials)
    except AuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    operator = db.get(Operator, operator_id)
    if operator is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return operator


def get_current_agent(
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
    x_agent_id: Annotated[str | None, Header(alias="X-Agent-ID")] = None,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)] = None,
    db: Session = Depends(get_db),
) -> Agent:
    # 1. Resolve API Key
    api_key = x_api_key
    if not api_key and credentials and credentials.scheme.lower() == "bearer":
        api_key = credentials.credentials

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key",
        )

    # 2. Resolve Agent ID
    if not x_agent_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Agent ID",
        )

    try:
        agent_uuid = uuid.UUID(x_agent_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Agent ID format",
        )

    # 3. Authenticate Operator API Key
    key_hash = hash_api_key(api_key)
    api_key_record = db.scalar(
        select(OperatorApiKey).where(
            OperatorApiKey.key_hash == key_hash,
            OperatorApiKey.revoked_at.is_(None),
        )
    )
    if not api_key_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    # 4. Fetch Agent
    agent = db.get(Agent, agent_uuid)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Agent not found",
        )

    if not agent.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Agent is inactive",
        )

    # 5. Check Authorization
    if agent.operator_id != api_key_record.operator_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden",
        )

    return agent


def get_optional_agent(
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
    x_agent_id: Annotated[str | None, Header(alias="X-Agent-ID")] = None,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)] = None,
    db: Session = Depends(get_db),
) -> Agent | None:
    if not x_api_key and not (credentials and credentials.scheme.lower() == "bearer"):
        return None
    if not x_agent_id:
        return None
    return get_current_agent(
        x_api_key=x_api_key,
        x_agent_id=x_agent_id,
        credentials=credentials,
        db=db,
    )

