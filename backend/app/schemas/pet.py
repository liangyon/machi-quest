from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime
from enum import Enum


class MoodType(str, Enum):
    """Enum for pet mood states"""
    HAPPY = "happy"
    CONTENT = "content"
    NEUTRAL = "neutral"
    TIRED = "tired"
    HUNGRY = "hungry"
    SAD = "sad"
    EXCITED = "excited"


class PetSkill(BaseModel):
    """Schema for individual pet skills"""
    name: str
    level: int = Field(default=1, ge=1, le=100)
    xp: int = Field(default=0, ge=0)


class PetAppearance(BaseModel):
    """Schema for pet appearance customization"""
    color: str = Field(default="default")
    pattern: Optional[str] = None
    accessories: List[str] = Field(default_factory=list)
    size_modifier: float = Field(default=1.0, ge=0.5, le=2.0)


class PetInventoryItem(BaseModel):
    """Schema for items in pet inventory"""
    item_id: str
    quantity: int = Field(default=1, ge=1)
    equipped: bool = Field(default=False)


class PetStats(BaseModel):
    """Schema for pet combat/activity stats"""
    strength: int = Field(default=10, ge=1, le=100)
    intelligence: int = Field(default=10, ge=1, le=100)
    agility: int = Field(default=10, ge=1, le=100)
    endurance: int = Field(default=10, ge=1, le=100)
    charisma: int = Field(default=10, ge=1, le=100)


class PetState(BaseModel):
    """Schema for comprehensive pet state JSON"""
    # Basic vitals
    energy: int = Field(default=100, ge=0, le=100, description="Pet's current energy level")
    hunger: int = Field(default=0, ge=0, le=100, description="Pet's hunger level (0 = full, 100 = starving)")
    happiness: int = Field(default=80, ge=0, le=100, description="Pet's happiness level")
    health: int = Field(default=100, ge=0, le=100, description="Pet's health points")
    
    # Progression
    level: int = Field(default=1, ge=1, description="Pet's current level")
    xp: int = Field(default=0, ge=0, description="Current experience points")
    xp_to_next_level: int = Field(default=100, ge=0, description="XP needed for next level")
    
    # Mood and status
    mood: MoodType = Field(default=MoodType.CONTENT, description="Pet's current mood")
    status_effects: List[str] = Field(default_factory=list, description="Active status effects on pet")
    
    # Skills
    skills: Dict[str, PetSkill] = Field(
        default_factory=dict,
        description="Pet's learned skills and their levels"
    )
    
    # Appearance
    appearance: PetAppearance = Field(default_factory=PetAppearance)
    
    # Inventory
    inventory: List[PetInventoryItem] = Field(
        default_factory=list,
        max_length=50,
        description="Items owned by the pet"
    )
    
    # Stats
    stats: PetStats = Field(default_factory=PetStats)
    
    # Achievements and milestones
    achievements: List[str] = Field(default_factory=list, description="Unlocked achievements")
    total_events_completed: int = Field(default=0, ge=0)
    total_time_played_minutes: int = Field(default=0, ge=0)
    
    # Activity tracking
    last_event_id: Optional[UUID] = None
    last_fed_at: Optional[datetime] = None
    last_played_at: Optional[datetime] = None
    last_update: Optional[datetime] = None
    
    # Relationship and bonding
    bond_level: int = Field(default=1, ge=1, le=10, description="Bond level with owner")
    bond_xp: int = Field(default=0, ge=0)
    
    # Custom traits and personality
    traits: Dict[str, Any] = Field(
        default_factory=dict,
        description="Custom traits and personality attributes"
    )
    
    # Daily/weekly streaks
    daily_login_streak: int = Field(default=0, ge=0)
    last_login_date: Optional[datetime] = None


class PetBase(BaseModel):
    """Base schema for pet with common attributes"""
    name: Optional[str] = Field(None, max_length=100, description="Pet's display name")
    species: Optional[str] = Field(default="default", max_length=50, description="Pet species/type")
    description: Optional[str] = Field(None, max_length=500, description="Custom pet description")


class PetCreate(PetBase):
    """Schema for creating a new pet"""
    pass


class PetUpdate(BaseModel):
    """Schema for updating pet information"""
    name: Optional[str] = Field(None, max_length=100)
    species: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = Field(None, max_length=500)
    state_json: Optional[PetState] = None


class PetResponse(PetBase):
    """Schema for pet response with full details"""
    id: UUID
    user_id: UUID
    description: Optional[str] = None
    state_json: PetState
    version: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PetStatsResponse(BaseModel):
    """Schema for pet statistics summary"""
    pet_id: UUID
    name: str
    species: str
    level: int
    xp: int
    health: int
    energy: int
    happiness: int
    bond_level: int
    total_events_completed: int
    achievements_count: int
    mood: MoodType


class PetFeedRequest(BaseModel):
    """Schema for feeding a pet"""
    food_item: str = Field(..., description="Type of food to feed the pet")
    quantity: int = Field(default=1, ge=1, le=10)


class PetPlayRequest(BaseModel):
    """Schema for playing with a pet"""
    activity: str = Field(..., description="Type of activity to do with pet")
    duration_minutes: int = Field(default=5, ge=1, le=60)
