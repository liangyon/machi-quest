"""
User model - represents application users.
"""
from sqlalchemy import Column, String, Text, Integer, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from .base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(Text, nullable=True)  # Nullable for OAuth-only users
    display_name = Column(String(100))
    avatar_url = Column(Text)
    github_id = Column(String(100), unique=True, nullable=True, index=True)
    github_username = Column(String(100), nullable=True)
    google_id = Column(String(100), unique=True, nullable=True, index=True)
    
    # Medallion currency for achievement system
    medallions = Column(Integer, default=0, nullable=False)
    
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    integrations = relationship("Integration", back_populates="user", cascade="all, delete-orphan")
    events = relationship("Event", back_populates="user", cascade="all, delete-orphan")
    goals = relationship("Goal", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")
    avatar = relationship("Avatar", back_populates="user", uselist=False, cascade="all, delete-orphan")
