from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime


class AvatarBase(BaseModel):
    """Base schema for avatar with common attributes"""
    species: str = Field(..., max_length=50, description="Avatar species (default, cat, etc.)")
    customization_json: Dict[str, Any] = Field(
        default_factory=dict,
        description="Custom appearance settings (colors, accessories, etc.)"
    )


class AvatarCreate(AvatarBase):
    """Schema for creating a new avatar"""
    pass


class AvatarUpdate(BaseModel):
    """Schema for updating avatar (partial updates allowed)"""
    species: Optional[str] = Field(None, max_length=50)
    customization_json: Optional[Dict[str, Any]] = None


class AvatarResponse(AvatarBase):
    """Schema for avatar response with full details"""
    id: UUID
    user_id: UUID
    state_json: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AvatarPreview(BaseModel):
    """Schema for previewing avatar appearance before creation"""
    species: str
    customization_json: Dict[str, Any]
    preview_url: Optional[str] = None
