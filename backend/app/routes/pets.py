from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID
import logging

from ..db.database import get_db
from ..db.models import User, Pet
from ..schemas.pet import PetCreate, PetResponse, PetUpdate, PetState
from ..core.dependencies import get_current_user
from ..services.cache import CacheService, pet_state_key
from ..core.config import settings
from ..repositories.pet_repository import PetRepository

logger = logging.getLogger(__name__)
cache = CacheService(settings.REDIS_URL)
router = APIRouter(prefix="/pets", tags=["Pets"])


@router.post("", response_model=PetResponse, status_code=status.HTTP_201_CREATED)
async def create_pet(
    pet_data: PetCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    pet_repo = PetRepository(db)
    default_state = PetState()
    
    new_pet = Pet(
        user_id=current_user.id,
        name=pet_data.name or "My Pet",
        species=pet_data.species or "default",
        description=pet_data.description,
        state_json=default_state.model_dump(),
        version=1
    )
    
    return await pet_repo.create(new_pet)


@router.get("", response_model=List[PetResponse])
async def get_user_pets(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    pet_repo = PetRepository(db)
    return await pet_repo.get_by_user_id(current_user.id)


@router.get("/{pet_id}", response_model=PetResponse)
async def get_pet(
    pet_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    pet_repo = PetRepository(db)
    pet = await pet_repo.get_by_id_and_user(pet_id, current_user.id)
    
    if not pet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pet not found or you don't have permission to access it"
        )
    
    return pet


@router.get("/{pet_id}/state", response_model=PetState)
async def get_pet_state(
    pet_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    pet_repo = PetRepository(db)
    cache_key = pet_state_key(str(pet_id))
    
    cached_state = cache.get(cache_key)
    if cached_state is not None:
        logger.debug(f"Cache HIT for pet {pet_id} state")
        return PetState(**cached_state)
    
    logger.debug(f"Cache MISS for pet {pet_id} state")
    pet = await pet_repo.get_by_id_and_user(pet_id, current_user.id)
    
    if not pet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pet not found or you don't have permission to access it"
        )
    
    if not pet.state_json or pet.state_json == {}:
        state_data = {
            "food": 0,
            "currency": 0,
            "happiness": 50,
            "health": 100,
            "processed_events": [],
            "food_cap": 100,
            "overflow_to_currency_rate": 0.5
        }
    else:
        state_data = pet.state_json
    
    cache.set(cache_key, state_data, ttl_seconds=300)
    return PetState(**state_data)


@router.patch("/{pet_id}", response_model=PetResponse)
async def update_pet(
    pet_id: UUID,
    pet_update: PetUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    pet_repo = PetRepository(db)
    pet = await pet_repo.get_by_id_and_user(pet_id, current_user.id)
    
    if not pet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pet not found or you don't have permission to access it"
        )
    
    if pet_update.name is not None:
        pet.name = pet_update.name
    
    if pet_update.species is not None:
        pet.species = pet_update.species
    
    if pet_update.description is not None:
        pet.description = pet_update.description
    
    if pet_update.state_json is not None:
        pet.state_json = pet_update.state_json.model_dump()
        await pet_repo.increment_version(pet)
        
        cache_key = pet_state_key(str(pet_id))
        cache.delete(cache_key)
        logger.info(f"Invalidated cache for pet {pet_id}")
    else:
        await pet_repo.update(pet)
    
    return pet


@router.delete("/{pet_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pet(
    pet_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    pet_repo = PetRepository(db)
    pet = await pet_repo.get_by_id_and_user(pet_id, current_user.id)
    
    if not pet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pet not found or you don't have permission to access it"
        )
    
    cache_key = pet_state_key(str(pet_id))
    cache.delete(cache_key)
    await pet_repo.delete(pet)
    
    return None


@router.get("/metrics/cache", response_model=dict)
async def get_cache_metrics(current_user: User = Depends(get_current_user)):
    metrics = cache.get_metrics()
    return {
        "cache_metrics": metrics,
        "message": f"Hit rate: {metrics['hit_rate_percent']}%"
    }
