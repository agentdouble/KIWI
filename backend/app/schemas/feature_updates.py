from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class FeatureUpdateSection(BaseModel):
    title: str
    items: List[str]


class FeatureUpdatesResponse(BaseModel):
    active: bool
    title: str
    sections: List[FeatureUpdateSection]
    updated_at: Optional[datetime] | None = None


class FeatureUpdatesUpdateRequest(BaseModel):
    active: bool
    title: str
    sections: List[FeatureUpdateSection]

