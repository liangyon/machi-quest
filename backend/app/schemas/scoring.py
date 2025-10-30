"""
Scoring schemas.

Defines the structure of score deltas - changes to pet state
caused by events.
"""
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID
from typing import Optional


class DeltaType:
    """
    Constants for score delta types.
    
    These represent the different stats that can change in pet state.
    """
    FOOD = "food"           # Food units for pet to consume
    CURRENCY = "currency"   # Coins/money for spending
    HAPPINESS = "happiness" # Happiness/mood stat
    HEALTH = "health"       # Health/wellbeing stat


class ScoreDelta(BaseModel):
    """
    Represents a change to pet state caused by an event.
    
    This is the output of the scoring engine and input to the state worker.
    The state worker reads these from the queue and applies them to Pet.state_json.
    
    Example:
        User commits 3 times → Scoring engine creates:
        ScoreDelta(
            delta_type="energy",
            amount=3.0,
            event_id=event_id,
            pet_id=pet_id
        )
    """
    delta_type: str = Field(..., description="Type of stat to change: 'food', 'currency', 'happiness', 'health'")
    amount: float = Field(..., description="How much to change (positive or negative)")
    event_id: UUID = Field(..., description="Which event caused this delta")
    pet_id: UUID = Field(..., description="Which pet to update")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When this delta was created")
    meta: dict = Field(default_factory=dict, description="Additional context")
    
    class Config:
        json_schema_extra = {
            "example": {
                "delta_type": "food",
                "amount": 5.0,
                "event_id": "12345678-1234-1234-1234-123456789012",
                "pet_id": "87654321-4321-4321-4321-210987654321",
                "timestamp": "2025-10-28T14:30:00Z",
                "meta": {"event_type": "github_commit", "commit_count": 5}
            }
        }
