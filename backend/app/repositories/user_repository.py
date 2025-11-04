from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .base_repository import BaseRepository
from ..db.models import User


class UserRepository(BaseRepository[User]):
    def __init__(self, db: AsyncSession):
        super().__init__(User, db)

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.db.execute(
            select(self.model).where(self.model.email == email)
        )
        return result.scalar_one_or_none()
    
    async def get_by_github_id(self, github_id: str) -> Optional[User]:
        result = await self.db.execute(
            select(self.model).where(self.model.github_id == github_id)
        )
        return result.scalar_one_or_none()
    
    async def email_exists(self, email: str) -> bool:
        result = await self.db.execute(
            select(self.model).where(self.model.email == email)
        )
        return result.scalar_one_or_none() is not None