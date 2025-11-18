from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class AlertResponse(BaseModel):
    message: str
    active: bool
    updated_at: Optional[datetime] | None = None


class AlertUpdateRequest(BaseModel):
    message: str
    active: bool

