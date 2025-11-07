"""
Integration model - OAuth and webhook integrations.
"""
from sqlalchemy import Column, String, LargeBinary, TIMESTAMP, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from .base import Base, JSONB


class Integration(Base):
    __tablename__ = "integrations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    provider = Column(String(50), nullable=False)
    access_token_encrypted = Column(LargeBinary)
    refresh_token_encrypted = Column(LargeBinary)
    meta_data = Column(JSONB, default={}, name="metadata")
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="integrations")
    event_raws = relationship("EventRaw", back_populates="integration", cascade="all, delete-orphan")
    goals = relationship("Goal", back_populates="integration")

    __table_args__ = (
        Index("idx_integrations_user_provider", "user_id", "provider"),
    )
