from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from agentnet_api.auth.github import fetch_github_user
from agentnet_api.auth.security import create_access_token, generate_api_key
from agentnet_api.db.models import Operator, OperatorApiKey
from agentnet_api.dependencies import get_current_operator, get_db
from agentnet_api.schemas.auth import (
    ApiKeyCreateRequest,
    ApiKeyMetadata,
    ApiKeyResponse,
    AuthRequest,
    AuthResponse,
    OperatorResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: AuthRequest, db: Session = Depends(get_db)) -> AuthResponse:
    github_user = await fetch_github_user(
        code=payload.code,
        github_id=payload.github_id,
        name=payload.name,
        email=payload.email,
    )

    existing = db.scalar(select(Operator).where(Operator.github_id == github_user.github_id))
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Operator already registered")

    operator = Operator(
        github_id=github_user.github_id,
        name=github_user.name,
        email=github_user.email,
    )
    db.add(operator)
    db.flush()
    db.refresh(operator)

    return AuthResponse(
        access_token=create_access_token(operator.id),
        operator=OperatorResponse.model_validate(operator),
    )


@router.post("/login", response_model=AuthResponse)
async def login(payload: AuthRequest, db: Session = Depends(get_db)) -> AuthResponse:
    github_user = await fetch_github_user(
        code=payload.code,
        github_id=payload.github_id,
        name=payload.name,
        email=payload.email,
    )

    operator = db.scalar(select(Operator).where(Operator.github_id == github_user.github_id))
    if operator is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Operator not registered")

    if github_user.email and operator.email != github_user.email:
        operator.email = github_user.email
    if operator.name != github_user.name:
        operator.name = github_user.name
    db.flush()
    db.refresh(operator)

    return AuthResponse(
        access_token=create_access_token(operator.id),
        operator=OperatorResponse.model_validate(operator),
    )
