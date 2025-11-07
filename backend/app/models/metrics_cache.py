"""
MetricsCache model - caches computed metrics for performance.
"""
from sqlalchemy import Column, String, Float, TIMESTAMP
from sqlalchemy.sql import func

from .base import Base


class MetricsCache(Base):
    __tablename__ = "metrics_cache"

    key = Column(String(100), primary_key=True)
    value = Column(Float)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
