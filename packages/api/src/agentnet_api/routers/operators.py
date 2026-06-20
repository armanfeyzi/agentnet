from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from agentnet_api.auth.security import generate_api_key
from agentnet_api.db.models import Operator, OperatorApiKey
from agentnet_api.dependencies import get_current_operator, get_db
from agentnet_api.schemas.auth import ApiKeyCreateRequest, ApiKeyResponse, OperatorResponse

router = APIRouter(prefix="/operators", tags=["operators"])


@router.get("/me", response_model=OperatorResponse)
def get_current_operator_profile(operator: Operator = Depends(get_current_operator)) -> Operator:
    return operator


@router.post("/me/api-keys", response_model=ApiKeyResponse, status_code=201)
def create_api_key(
    payload: ApiKeyCreateRequest,
    operator: Operator = Depends(get_current_operator),
    db: Session = Depends(get_db),
) -> ApiKeyResponse:
    api_key, key_prefix, key_hash = generate_api_key()
    record = OperatorApiKey(
        operator_id=operator.id,
        name=payload.name,
        key_prefix=key_prefix,
        key_hash=key_hash,
    )
    db.add(record)
    db.flush()
    db.refresh(record)

    return ApiKeyResponse(
        id=record.id,
        name=record.name,
        key_prefix=record.key_prefix,
        api_key=api_key,
        created_at=record.created_at,
    )
