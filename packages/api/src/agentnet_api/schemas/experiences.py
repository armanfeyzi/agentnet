from typing import Literal
import uuid

from pydantic import BaseModel


class DraftResponse(BaseModel):
    draft_id: uuid.UUID
    status: Literal["pending_approval"]
