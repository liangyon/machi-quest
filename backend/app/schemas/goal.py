from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from uuid import UUID
from datetime import datetime


class GoalBase(BaseModel):
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    target_value: float = Field(default=1.0)
    unit: Optional[str] = Field(None, max_length=50)


class GoalCreate(GoalBase):
    pass


class GoalUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    target_value: Optional[float] = None
    current_value: Optional[float] = None
    unit: Optional[str] = Field(None, max_length=50)
    is_completed: Optional[bool] = None


class GoalResponse(GoalBase):
    id: UUID
    user_id: UUID
    current_value: float
    is_completed: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
