"""
Avatar model - user's visual representation in the achievement system.
"""
from sqlalchemy import Column, String, TIMESTAMP, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from .base import Base, JSONB


class Avatar(Base):
    """
    User's visual representation in the achievement system.
    Replaces the pet concept but without game mechanics.
    One avatar per user.
    """
    __tablename__ = "avatars"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    
    # Customization - species options: "default", "cat", etc.
    species = Column(String(50), default="default", nullable=False)
    customization_json = Column(JSONB, default={})
    state_json = Column(JSONB, default={})
    
    # Timestamps
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="avatar")
    
    __table_args__ = (
        Index("idx_avatars_user_id", "user_id"),
    )
