"""
Manual Event Normalizers

Handles user-submitted events that aren't auto-tracked.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from ..event_normalizer import CanonicalEvent, EventType


def normalize_manual_event(
    event_type: str,
    title: str,
    user_id: UUID,
    value: float = 1.0,
    meta: Optional[dict] = None,
    timestamp: Optional[datetime] = None,
    pet_id: Optional[UUID] = None
) -> CanonicalEvent:
    """
    Create a canonical event from manual user input.
    
    This is the fallback for anything not auto-tracked:
    - "Practiced guitar for 30 minutes"
    - "Read 50 pages"
    - "Watered plants"
    - "Meditated for 10 minutes"
    
    Args:
        event_type: Usually EventType.MANUAL_HABIT or MANUAL_GOAL_PROGRESS
        title: Human-readable description of what was done
        user_id: UUID of the user
        value: Scoring value (default 1.0)
        meta: Additional context (category, duration, etc.)
        timestamp: When it occurred (defaults to now)
        pet_id: Optional pet to credit
        
    Returns:
        Single CanonicalEvent
        
    Example usage:
        event = normalize_manual_event(
            event_type=EventType.MANUAL_HABIT,
            title="Practiced guitar",
            user_id=user_id,
            value=1.0,
            meta={'duration_minutes': 30, 'category': 'music'}
        )
    """
    if timestamp is None:
        timestamp = datetime.utcnow()
    
    if meta is None:
        meta = {}
    
    # Add title and source to metadata
    meta['title'] = title
    meta['source'] = 'manual'
    
    return CanonicalEvent(
        type=event_type,
        timestamp=timestamp,
        user_id=user_id,
        value=value,
        meta=meta,
        pet_id=pet_id
    )
