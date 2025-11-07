"""
Event models - raw events and normalized events.
"""
from sqlalchemy import Column, String, Float, Boolean, TIMESTAMP, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from .base import Base, JSONB


class EventRaw(Base):
    __tablename__ = "event_raw"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    integration_id = Column(UUID(as_uuid=True), ForeignKey("integrations.id"), nullable=True)
    external_event_id = Column(String(255), unique=True, index=True)
    payload = Column(JSONB, nullable=False)
    received_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    processed = Column(Boolean, default=False)

    # Relationships
    integration = relationship("Integration", back_populates="event_raws")
    events = relationship("Event", back_populates="event_raw", cascade="all, delete-orphan")


class Event(Base):
    __tablename__ = "events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_raw_id = Column(UUID(as_uuid=True), ForeignKey("event_raw.id"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # goal_id for new achievement system
    goal_id = Column(UUID(as_uuid=True), ForeignKey("goals.id"), nullable=True)
    
    type = Column(String(100), nullable=False)
    value = Column(Float, default=1.0)
    meta = Column(JSONB, default={})
    scored = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # Relationships
    event_raw = relationship("EventRaw", back_populates="events")
    user = relationship("User", back_populates="events")
    goal = relationship("Goal", back_populates="events")

    __table_args__ = (
        Index("idx_events_user_created", "user_id", "created_at"),
        Index("idx_events_goal_id", "goal_id"),
    )
