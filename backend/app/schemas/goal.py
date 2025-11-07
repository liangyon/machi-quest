from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime, date

from ..types import GoalType, TrackingType, IntegrationSource, GrowthStage


class GoalBase(BaseModel):
    """Base schema for goal with common attributes"""
    name: str = Field(..., max_length=200, description="Goal name/title")
    description: Optional[str] = Field(None, description="Detailed goal description")
    goal_type: GoalType = Field(..., description="Goal type: long_term or short_term")
    integration_source: IntegrationSource = Field(
        default=IntegrationSource.MANUAL,
        description="Source of goal updates (github, strava, manual)"
    )
    tracking_type: TrackingType = Field(
        default=TrackingType.BINARY,
        description="How progress is tracked"
    )
    target_value: int = Field(..., gt=0, description="Target value to reach for completion")
    unit: Optional[str] = Field(None, max_length=50, description="Unit of measurement (commits, runs, tasks)")
    visual_variant: Optional[str] = Field(None, max_length=50, description="Visual representation (farm/animal type)")
    deadline: Optional[datetime] = Field(None, description="Optional deadline for goal")


class GoalCreate(GoalBase):
    """Schema for creating a new goal"""
    integration_id: Optional[UUID] = Field(None, description="Link to specific integration if applicable")


class GoalUpdate(BaseModel):
    """Schema for updating goal (partial updates allowed)"""
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    target_value: Optional[int] = Field(None, gt=0)
    unit: Optional[str] = Field(None, max_length=50)
    visual_variant: Optional[str] = Field(None, max_length=50)
    deadline: Optional[datetime] = None
    is_completed: Optional[bool] = None


class GoalResponse(GoalBase):
    """Schema for goal response with full details including calculated progress"""
    id: UUID
    user_id: UUID
    integration_id: Optional[UUID]
    current_progress: int
    is_completed: bool
    is_crowned: bool
    completed_at: Optional[datetime]
    last_completed_date: Optional[date]
    total_medallions_produced: int
    growth_stage: int
    state_json: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    
    # Computed progress metrics (calculated on the fly)
    @property
    def progress_percentage(self) -> float:
        """Calculate progress as percentage"""
        if self.target_value == 0:
            return 0.0
        return min(100.0, (self.current_progress / self.target_value) * 100)

    model_config = ConfigDict(from_attributes=True)


class GoalStats(BaseModel):
    """Schema for aggregated goal statistics"""
    total_goals: int
    active_goals: int
    completed_goals: int
    crowned_goals: int
    total_medallions_earned: int
    average_completion_rate: float
    longest_streak: int
    current_streak: int


class GoalCrownRequest(BaseModel):
    """Schema for manually crowning a short-term goal"""
    pass  # Empty body, goal_id comes from path parameter
