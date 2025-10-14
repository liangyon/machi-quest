from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime


class IntegrationBase(BaseModel):
    provider: str = Field(..., max_length=50)
    meta_data: Dict[str, Any] = Field(default_factory=dict)


class IntegrationCreate(IntegrationBase):
    access_token: str
    refresh_token: Optional[str] = None


class IntegrationUpdate(BaseModel):
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    meta_data: Optional[Dict[str, Any]] = None


class IntegrationResponse(BaseModel):
    id: UUID
    user_id: UUID
    provider: str
    meta_data: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
