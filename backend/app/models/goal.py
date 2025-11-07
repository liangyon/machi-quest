"""
Goal model - core entity for the achievement system.
"""
from sqlalchemy import Column, String, Text, Integer, Boolean, Date, TIMESTAMP, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from .base import Base, JSONB


class Goal(Base):
    """
    Enhanced Goal model for the achievement system.
    Goals are now the core game entity, tracking progress and awarding medallions.
    """
    __tablename__ = "goals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    
    # Goal classification
    goal_type = Column(String(20), nullable=False)  # 'long_term' or 'short_term'
    integration_source = Column(String(50))  # 'github', 'strava', 'manual'
    integration_id = Column(UUID(as_uuid=True), ForeignKey("integrations.id"))
    tracking_type = Column(String(20), default='binary')  # 'binary' or 'numeric'
    
    # Progress tracking (Integer for clearer counting)
    current_progress = Column(Integer, default=0)
    target_value = Column(Integer, nullable=False)
    unit = Column(String(50))  # Optional unit (e.g., "commits", "runs", "tasks")
    
    # Completion tracking
    is_completed = Column(Boolean, default=False)
    is_crowned = Column(Boolean, default=False)  # True when target reached
    completed_at = Column(TIMESTAMP(timezone=True))
    last_completed_date = Column(Date)  # Track last daily completion for medallion limits
    
    # Medallion economy
    total_medallions_produced = Column(Integer, default=0)
    
    # Visual representation (farm plot or animal type)
    visual_variant = Column(String(50))
    growth_stage = Column(Integer, default=0)  # 0-3: baby, teen, adult, crowned
    state_json = Column(JSONB, default={})
    
    # Optional deadline for time-bound goals
    deadline = Column(TIMESTAMP(timezone=True))
    
    # Timestamps
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="goals")
    integration = relationship("Integration", back_populates="goals")
    events = relationship("Event", back_populates="goal")

    __table_args__ = (
        Index("idx_goals_user_completed", "user_id", "is_completed"),
        Index("idx_goals_integration", "integration_id"),
        Index("idx_goals_user_type", "user_id", "goal_type"),
    )
