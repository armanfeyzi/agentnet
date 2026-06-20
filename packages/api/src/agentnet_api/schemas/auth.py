import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class AuthRequest(BaseModel):
    code: str | None = None
    github_id: str | None = None
    name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = None


class OperatorResponse(BaseModel):
    id: uuid.UUID
    email: str | None
    name: str
    github_id: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    operator: OperatorResponse


class ApiKeyCreateRequest(BaseModel):
    name: str | None = Field(default=None, max_length=255)


class ApiKeyResponse(BaseModel):
    id: uuid.UUID
    name: str | None
    key_prefix: str
    api_key: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ApiKeyMetadata(BaseModel):
    id: uuid.UUID
    name: str | None
    key_prefix: str
    created_at: datetime
    revoked_at: datetime | None

    model_config = ConfigDict(from_attributes=True)
