from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime


class EventRawCreate(BaseModel):
    integration_id: UUID
    external_event_id: str = Field(..., max_length=255)
    payload: Dict[str, Any]


class EventRawResponse(BaseModel):
    id: UUID
    integration_id: UUID
    external_event_id: str
    payload: Dict[str, Any]
    received_at: datetime
    processed: bool

    model_config = ConfigDict(from_attributes=True)


class EventBase(BaseModel):
    type: str = Field(..., max_length=100)
    value: float = Field(default=1.0)
    meta: Dict[str, Any] = Field(default_factory=dict)


class EventCreate(EventBase):
    event_raw_id: Optional[UUID] = None
    user_id: UUID
    pet_id: Optional[UUID] = None


class EventUpdate(BaseModel):
    scored: Optional[bool] = None


class EventResponse(EventBase):
    id: UUID
    event_raw_id: Optional[UUID]
    user_id: UUID
    pet_id: Optional[UUID]
    scored: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
