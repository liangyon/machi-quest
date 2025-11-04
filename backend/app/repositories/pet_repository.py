from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .base_repository import BaseRepository
from ..db.models import Pet

class PetRepository(BaseRepository[Pet]):
    def __init__(self, db: AsyncSession):
        super().__init__(Pet, db)

    async def get_by_user_id(self, user_id: UUID) -> Optional[Pet]:
        """Get all pets owned by a specific user."""
        result = await self.db.execute(
            select(self.model).where(self.model.user_id == user_id)
        )
        return result.scalars().all()

    async def get_by_id_and_user(self, pet_id: UUID, user_id: UUID) -> Optional[Pet]:
        result = await self.db.execute(
            select(self.model).where(self.model.id == pet_id, self.model.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def increment_version(self, pet: Pet) -> Pet:
        """Increment the version of the pet."""
        pet.version += 1
        return await self.update(pet)