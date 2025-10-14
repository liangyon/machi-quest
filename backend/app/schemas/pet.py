from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime


class PetState(BaseModel):
    """Schema for pet state JSON"""
    energy: int = Field(default=100, ge=0, le=100)
    hunger: int = Field(default=0, ge=0, le=100)
    level: int = Field(default=1, ge=1)
    xp: int = Field(default=0, ge=0)
    last_event_id: Optional[UUID] = None
    last_update: Optional[datetime] = None
    traits: Dict[str, Any] = Field(default_factory=dict)


class PetBase(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    species: Optional[str] = Field(default="default", max_length=50)


class PetCreate(PetBase):
    pass


class PetUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    species: Optional[str] = Field(None, max_length=50)
    state_json: Optional[PetState] = None


class PetResponse(PetBase):
    id: UUID
    user_id: UUID
    state_json: PetState
    version: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
