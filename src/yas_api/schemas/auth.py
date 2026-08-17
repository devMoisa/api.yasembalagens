from datetime import datetime

from pydantic import BaseModel

from yas_api.schemas.common import ORMModel


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AdminUserRead(ORMModel):
    id: int
    name: str
    email: str
    is_active: bool
    created_at: datetime
