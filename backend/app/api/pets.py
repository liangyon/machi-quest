from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from ..db.database import get_db
from ..db.models import User, Pet
from ..schemas.pet import PetCreate, PetResponse, PetUpdate, PetState
from ..core.dependencies import get_current_user

router = APIRouter(prefix="/pets", tags=["Pets"])


@router.post("", response_model=PetResponse, status_code=status.HTTP_201_CREATED)
def create_pet(
    pet_data: PetCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new pet for the authenticated user.
    
    The pet will be initialized with default state values:
    - Energy: 100
    - Hunger: 0
    - Level: 1
    - XP: 0
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
    db.commit()
    db.refresh(new_pet)
    
    return new_pet


@router.get("", response_model=List[PetResponse])
def get_user_pets(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all pets belonging to the authenticated user.
    
    Returns a list of all pets owned by the current user.
    """
    pets = db.query(Pet).filter(Pet.user_id == current_user.id).all()
    return pets


@router.get("/{pet_id}", response_model=PetResponse)
def get_pet(
    pet_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific pet by ID.
    
    The pet must belong to the authenticated user.
    """
    pet = db.query(Pet).filter(
        Pet.id == pet_id,
        Pet.user_id == current_user.id
    ).first()
    
    if not pet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pet not found or you don't have permission to access it"
        )
    
    return pet


@router.patch("/{pet_id}", response_model=PetResponse)
def update_pet(
    pet_id: UUID,
    pet_update: PetUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a pet's information.
    
    You can update the pet's name, species, or state.
    Only pets belonging to the authenticated user can be updated.
    """
    pet = db.query(Pet).filter(
        Pet.id == pet_id,
        Pet.user_id == current_user.id
    ).first()
    
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
    
    db.commit()
    db.refresh(pet)
    
    return pet


@router.delete("/{pet_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_pet(
    pet_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a pet.
    
    Only pets belonging to the authenticated user can be deleted.
    This will also delete all associated events.
    """
    pet = db.query(Pet).filter(
        Pet.id == pet_id,
        Pet.user_id == current_user.id
    ).first()
    
    if not pet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pet not found or you don't have permission to access it"
        )
    
    db.delete(pet)
    db.commit()
    
    return None
