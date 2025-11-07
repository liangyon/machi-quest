"""
Base model and shared type decorators.
"""
from sqlalchemy import TypeDecorator, Text
from sqlalchemy.dialects.postgresql import JSONB as PostgreSQL_JSONB
from sqlalchemy.ext.declarative import declarative_base
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
