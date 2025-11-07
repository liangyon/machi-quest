from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.database import get_db
from ..models import User
from ..schemas.avatar import AvatarResponse, AvatarCreate, AvatarUpdate, AvatarPreview
from ..repositories.avatar_repository import AvatarRepository
from ..core.dependencies import get_current_user

router = APIRouter(prefix="/avatars", tags=["Avatars"])


@router.get("/me", response_model=AvatarResponse)
async def get_my_avatar(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user's avatar (creates default if doesn't exist)"""
    repo = AvatarRepository(db)
    avatar = await repo.get_or_create_avatar(current_user.id)
    return avatar


@router.post("", response_model=AvatarResponse, status_code=status.HTTP_201_CREATED)
async def create_avatar(
    avatar_data: AvatarCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create avatar for current user.
    Note: Avatar is auto-created on registration, so this is mainly for re-creation.
    """
    repo = AvatarRepository(db)
    
    # Check if avatar already exists
    existing = await repo.get_by_user_id(current_user.id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already has an avatar. Use PATCH /avatars/me to update."
        )
    
    avatar = await repo.create_default_avatar(
        user_id=current_user.id,
        species=avatar_data.species
    )
    
    # Update customization if provided
    if avatar_data.customization_json:
        avatar.customization_json = avatar_data.customization_json
        avatar = await repo.update(avatar)
    
    return avatar


@router.patch("/me", response_model=AvatarResponse)
async def update_my_avatar(
    avatar_update: AvatarUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update current user's avatar customization"""
    repo = AvatarRepository(db)
    
    # Get or create avatar
    avatar = await repo.get_or_create_avatar(current_user.id)
    
    # Update fields
    if avatar_update.species is not None:
        avatar.species = avatar_update.species
    
    if avatar_update.customization_json is not None:
        avatar.customization_json = avatar_update.customization_json
    
    avatar = await repo.update(avatar)
    return avatar


@router.get("/preview", response_model=AvatarPreview)
async def preview_avatar_species(
    species: str = "default",
    current_user: User = Depends(get_current_user)
):
    """Preview how an avatar species would look"""
    # This is a simple preview endpoint
    # In a real implementation, this might fetch from a CDN or generate preview images
    return AvatarPreview(
        species=species,
        customization_json={},
        preview_url=f"/static/avatars/{species}.png"  # Placeholder
    )
