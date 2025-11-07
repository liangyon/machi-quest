from typing import Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .base_repository import BaseRepository
from ..models import Avatar, User


class AvatarRepository(BaseRepository[Avatar]):
    def __init__(self, db: AsyncSession):
        super().__init__(Avatar, db)

    async def get_by_user_id(self, user_id: UUID) -> Optional[Avatar]:
        """Get avatar by user ID"""
        result = await self.db.execute(
            select(self.model).where(self.model.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create_default_avatar(self, user_id: UUID, species: str = "default") -> Avatar:
        """Create a default avatar for a user"""
        avatar = Avatar(
            user_id=user_id,
            species=species,
            customization_json={},
            state_json={}
        )
        return await self.create(avatar)

    async def get_or_create_avatar(self, user_id: UUID, species: str = "default") -> Avatar:
        """Get existing avatar or create a new one if it doesn't exist"""
        avatar = await self.get_by_user_id(user_id)
        if avatar is None:
            avatar = await self.create_default_avatar(user_id, species)
        return avatar

    async def update_customization(
        self, 
        avatar_id: UUID, 
        customization_json: dict
    ) -> Optional[Avatar]:
        """Update avatar customization"""
        avatar = await self.get_by_id(avatar_id)
        if avatar:
            avatar.customization_json = customization_json
            return await self.update(avatar)
        return None

    async def update_species(self, avatar_id: UUID, species: str) -> Optional[Avatar]:
        """Update avatar species"""
        avatar = await self.get_by_id(avatar_id)
        if avatar:
            avatar.species = species
            return await self.update(avatar)
        return None
