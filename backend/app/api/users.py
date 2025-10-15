from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db.database import get_db
from ..db.models import User
from ..schemas.user import UserWithPets
from ..core.dependencies import get_current_user

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserWithPets)
def get_current_user_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current authenticated user's information including pet references.
    """
    # Get pet IDs for the current user
    pet_ids = [pet.id for pet in current_user.pets]
    
    # Create response with pet references
    user_data = UserWithPets(
        id=current_user.id,
        email=current_user.email,
        display_name=current_user.display_name,
        avatar_url=current_user.avatar_url,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
        pets=pet_ids
    )
    
    return user_data
