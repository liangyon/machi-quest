from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID
import logging

from ..db.database import get_db
from ..db.models import User, Pet
from ..schemas.pet import PetCreate, PetResponse, PetUpdate, PetState
from ..core.dependencies import get_current_user
from ..services.cache import CacheService, pet_state_key
from ..core.config import settings

logger = logging.getLogger(__name__)

# Initialize cache service
cache = CacheService(settings.REDIS_URL)

router = APIRouter(prefix="/pets", tags=["Pets"])


@router.post("", response_model=PetResponse, status_code=status.HTTP_201_CREATED)
async def create_pet(
    pet_data: PetCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new pet for the authenticated user.
    
    The pet will be initialized with default state values.
    """
    # Initialize default pet state
    default_state = PetState()
    
    # Create new pet
    new_pet = Pet(
        user_id=current_user.id,
        name=pet_data.name or "My Pet",
        species=pet_data.species or "default",
        description=pet_data.description,
        state_json=default_state.model_dump(),
        version=1
    )
    
    db.add(new_pet)
    await db.commit()
    await db.refresh(new_pet)
    
    return new_pet


@router.get("", response_model=List[PetResponse])
async def get_user_pets(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all pets belonging to the authenticated user.
    """
    result = await db.execute(select(Pet).where(Pet.user_id == current_user.id))
    pets = result.scalars().all()
    return pets


@router.get("/{pet_id}", response_model=PetResponse)
async def get_pet(
    pet_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific pet by ID.
    
    The pet must belong to the authenticated user.
    """
    result = await db.execute(
        select(Pet).where(Pet.id == pet_id, Pet.user_id == current_user.id)
    )
    pet = result.scalar_one_or_none()
    
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
    """
    Get a pet's current state with Redis caching.
    
    This endpoint is optimized for frequent polling by the frontend.
    State is cached in Redis for 5 minutes and invalidated on updates.
    
    Returns:
        PetState: Current pet state (food, currency, happiness, health, etc.)
    """
    cache_key = pet_state_key(str(pet_id))
    
    # Try to get from cache first
    cached_state = cache.get(cache_key)
    if cached_state is not None:
        logger.debug(f"Cache HIT for pet {pet_id} state")
        return PetState(**cached_state)
    
    # Cache miss - fetch from database
    logger.debug(f"Cache MISS for pet {pet_id} state")
    
    result = await db.execute(
        select(Pet).where(Pet.id == pet_id, Pet.user_id == current_user.id)
    )
    pet = result.scalar_one_or_none()
    
    if not pet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pet not found or you don't have permission to access it"
        )
    
    # Get state (with defaults if not initialized)
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
    
    # Cache the state
    cache.set(cache_key, state_data, ttl_seconds=300)  # 5 minute TTL
    
    return PetState(**state_data)


@router.patch("/{pet_id}", response_model=PetResponse)
async def update_pet(
    pet_id: UUID,
    pet_update: PetUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a pet's information.
    
    You can update the pet's name, species, or state.
    Invalidates cache on state changes.
    """
    result = await db.execute(
        select(Pet).where(Pet.id == pet_id, Pet.user_id == current_user.id)
    )
    pet = result.scalar_one_or_none()
    
    if not pet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pet not found or you don't have permission to access it"
        )
    
    # Update fields if provided
    if pet_update.name is not None:
        pet.name = pet_update.name
    
    if pet_update.species is not None:
        pet.species = pet_update.species
    
    if pet_update.description is not None:
        pet.description = pet_update.description
    
    if pet_update.state_json is not None:
        pet.state_json = pet_update.state_json.model_dump()
        pet.version += 1  # Increment version on state change
        
        # Invalidate cache since state changed
        cache_key = pet_state_key(str(pet_id))
        cache.delete(cache_key)
        logger.info(f"Invalidated cache for pet {pet_id}")
    
    await db.commit()
    await db.refresh(pet)
    
    return pet


@router.delete("/{pet_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pet(
    pet_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a pet.
    
    Only pets belonging to the authenticated user can be deleted.
    This will also delete all associated events.
    """
    result = await db.execute(
        select(Pet).where(Pet.id == pet_id, Pet.user_id == current_user.id)
    )
    pet = result.scalar_one_or_none()
    
    if not pet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pet not found or you don't have permission to access it"
        )
    
    # Invalidate cache before deleting
    cache_key = pet_state_key(str(pet_id))
    cache.delete(cache_key)
    
    await db.delete(pet)
    await db.commit()
    
    return None


@router.get("/metrics/cache", response_model=dict)
async def get_cache_metrics(
    current_user: User = Depends(get_current_user)
):
    """
    Get cache performance metrics.
    
    Returns hit/miss statistics for monitoring cache effectiveness.
    """
    metrics = cache.get_metrics()
    return {
        "cache_metrics": metrics,
        "message": f"Hit rate: {metrics['hit_rate_percent']}%"
    }
