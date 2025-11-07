from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker, Session
from typing import AsyncGenerator
import os

# Database URL from environment variable (sync version for init_db and alembic)
DATABASE_URL_SYNC = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/machi_quest"
)

# Convert to async version for asyncpg driver
DATABASE_URL = DATABASE_URL_SYNC.replace("postgresql://", "postgresql+asyncpg://")

# Convert to sync version with psycopg2 driver for workers and migrations
DATABASE_URL_SYNC_PSYCOPG2 = DATABASE_URL_SYNC.replace("postgresql://", "postgresql+psycopg2://")

# Create sync engine for workers and migrations
sync_engine = create_engine(
    DATABASE_URL_SYNC_PSYCOPG2,
    echo=os.getenv("SQL_ECHO", "false").lower() == "true",
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# Create sync session factory for workers and Alembic
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=sync_engine
)

# Create async engine for FastAPI endpoints
engine = create_async_engine(
    DATABASE_URL,
    echo=os.getenv("SQL_ECHO", "false").lower() == "true",
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# Create async session factory for FastAPI endpoints
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Important for async to prevent detached instance errors
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency function to get async database session.

    """
    async with AsyncSessionLocal() as session:
        yield session


def init_db() -> None:
    """
    Initialize database tables.
    This should be called on application startup 
    """
    from ..models import Base
    
    # Use the psycopg2 sync engine
    Base.metadata.create_all(bind=sync_engine)
