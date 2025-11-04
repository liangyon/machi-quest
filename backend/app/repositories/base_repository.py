from typing import List, Optional, TypeVar, Generic, Type
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select



ModelType = TypeVar("ModelType")


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], db: AsyncSession):
        self.model = model
        self.db = db
        
    async def get_by_id(self, id: UUID) -> Optional[ModelType]:
        result = await self.db.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()
    
    async def get_all(self) -> List[ModelType]:
        result = await self.db.execute(select(self.model))
        return result.scalars().all()
    
    async def create(self, obj_in: ModelType) -> ModelType:
        self.db.add(obj_in)
        await self.db.commit()
        await self.db.refresh(obj_in)
        return obj_in
    
    async def update(self, db_obj: ModelType) -> ModelType:
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj
    
    async def delete(self, db_obj: ModelType) -> None:
        await self.db.delete(db_obj)
        await self.db.commit()