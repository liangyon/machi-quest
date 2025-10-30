from sqlalchemy import (
    Column, String, Text, Integer, Float, Boolean, 
    TIMESTAMP, ForeignKey, BigInteger, LargeBinary, Index, TypeDecorator
)
from sqlalchemy.dialects.postgresql import UUID, JSONB as PostgreSQL_JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import json


class JSONB(TypeDecorator):
    """
    Platform-independent JSONB type.
    
    Uses PostgreSQL JSONB in production, JSON/TEXT in SQLite for testing.
    """
    impl = Text
    cache_ok = True
    
    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PostgreSQL_JSONB())
        else:
            # SQLite: use TEXT and handle JSON serialization
            return dialect.type_descriptor(Text())
    
    def process_bind_param(self, value, dialect):
        if value is not None and dialect.name != 'postgresql':
            return json.dumps(value)
        return value
    
    def process_result_value(self, value, dialect):
        if value is not None and dialect.name != 'postgresql':
            return json.loads(value)
        return value

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(Text, nullable=True)  # Nullable for OAuth-only users
    display_name = Column(String(100))
    avatar_url = Column(Text)
    github_id = Column(String(100), unique=True, nullable=True, index=True)  # GitHub user ID
    github_username = Column(String(100), nullable=True)  # GitHub username
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    pets = relationship("Pet", back_populates="user", cascade="all, delete-orphan")
    integrations = relationship("Integration", back_populates="user", cascade="all, delete-orphan")
    events = relationship("Event", back_populates="user", cascade="all, delete-orphan")
    goals = relationship("Goal", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")


class Pet(Base):
    __tablename__ = "pets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String(100))
    species = Column(String(50), default="default")
    description = Column(String(500))
    state_json = Column(JSONB, default={})
    version = Column(Integer, default=1)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="pets")
    events = relationship("Event", back_populates="pet", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_pets_user_id", "user_id"),
    )


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

    __table_args__ = (
        Index("idx_integrations_user_provider", "user_id", "provider"),
    )


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
    pet_id = Column(UUID(as_uuid=True), ForeignKey("pets.id"))
    type = Column(String(100), nullable=False)
    value = Column(Float, default=1.0)
    meta = Column(JSONB, default={})
    scored = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # Relationships
    event_raw = relationship("EventRaw", back_populates="events")
    user = relationship("User", back_populates="events")
    pet = relationship("Pet", back_populates="events")

    __table_args__ = (
        Index("idx_events_user_created", "user_id", "created_at"),
    )


class Goal(Base):
    __tablename__ = "goals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    target_value = Column(Float, default=1.0)
    current_value = Column(Float, default=0.0)
    unit = Column(String(50))
    is_completed = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="goals")

    __table_args__ = (
        Index("idx_goals_user_completed", "user_id", "is_completed"),
    )


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    action = Column(String(100), nullable=False)
    target_type = Column(String(50))
    target_id = Column(UUID(as_uuid=True))
    meta_data = Column(JSONB, name="metadata")
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="audit_logs")


class MetricsCache(Base):
    __tablename__ = "metrics_cache"

    key = Column(String(100), primary_key=True)
    value = Column(Float)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
