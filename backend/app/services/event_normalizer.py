"""
Event Normalizer Service

Transforms external events (GitHub, Strava, manual, etc.) into a canonical
Event structure for consistent processing by the scoring engine.

This module defines the core types and re-exports normalizer functions
from source-specific modules.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID


class EventType:
    """
    Canonical event type constants.
    
    These represent our internal vocabulary for all event types,
    regardless of source (GitHub, Strava, manual, etc.).
    """
    # GitHub - Developer productivity
    GITHUB_COMMIT = "github_commit"
    GITHUB_PR_OPENED = "github_pr_opened"
    GITHUB_PR_MERGED = "github_pr_merged"
    GITHUB_PR_CLOSED = "github_pr_closed"
    GITHUB_COMMIT_COMMENT = "github_commit_comment"
    
    # Fitness & Health (future integrations)
    STRAVA_ACTIVITY = "strava_activity"
    APPLE_HEALTH_WORKOUT = "apple_health_workout"
    APPLE_HEALTH_STEPS = "apple_health_steps"
    
    # Learning & Productivity (future integrations)
    DUOLINGO_LESSON = "duolingo_lesson"
    TODOIST_TASK = "todoist_task"
    
    # Creative & Hobbies (future integrations)
    GOODREADS_BOOK = "goodreads_book"
    
    # Manual tracking (user-submitted)
    MANUAL_HABIT = "manual_habit"
    MANUAL_GOAL_PROGRESS = "manual_goal_progress"


@dataclass
class CanonicalEvent:
    """
    Normalized event structure used throughout the system.
    
    All external events (GitHub pushes, Strava runs, manual entries)
    are transformed into this canonical shape before scoring.
    
    Attributes:
        type: Event type constant from EventType class
        timestamp: When the event occurred (external source timestamp)
        user_id: UUID of the user who performed the action
        value: Base scoring value (typically 1.0, can be adjusted)
        meta: Event-specific metadata (commit SHA, workout distance, etc.)
        pet_id: Optional pet ID to credit (defaults to primary pet)
        event_raw_id: Optional link to the raw external event
    """
    type: str
    timestamp: datetime
    user_id: UUID
    value: float
    meta: dict
    
    # Optional fields
    pet_id: Optional[UUID] = None
    event_raw_id: Optional[UUID] = None
    
    def __post_init__(self):
        """Validate the event after initialization."""
        if not self.type:
            raise ValueError("Event type is required")
        if not self.user_id:
            raise ValueError("User ID is required")
        if self.value < 0:
            raise ValueError("Event value cannot be negative")


def validate_canonical_event(event: CanonicalEvent) -> None:
    """
    Validate that a canonical event is well-formed.
    
    Performs type-specific validation based on event type.
    
    Args:
        event: CanonicalEvent to validate
        
    Raises:
        ValueError: If event is invalid
    """
    # Basic validation (already done in __post_init__)
    if not event.type:
        raise ValueError("Event type is required")
    
    # Check if type is a known event type
    valid_types = {
        getattr(EventType, attr) 
        for attr in dir(EventType) 
        if not attr.startswith('_')
    }
    if event.type not in valid_types:
        raise ValueError(f"Invalid event type: {event.type}")
    
    # Type-specific validation
    if event.type == EventType.GITHUB_COMMIT:
        if 'commit_sha' not in event.meta:
            raise ValueError("GitHub commit events must include commit_sha in meta")
    
    elif event.type in [EventType.GITHUB_PR_OPENED, EventType.GITHUB_PR_MERGED, EventType.GITHUB_PR_CLOSED]:
        if 'pr_number' not in event.meta:
            raise ValueError("GitHub PR events must include pr_number in meta")
    
    elif event.type == EventType.MANUAL_HABIT:
        if 'title' not in event.meta:
            raise ValueError("Manual habit events must include title in meta")


# Re-export normalizer functions from source-specific modules
from .normalizers.github import (
    normalize_github_push,
    normalize_github_pull_request,
    normalize_github_commit_comment,
)
from .normalizers.manual import normalize_manual_event

__all__ = [
    'EventType',
    'CanonicalEvent',
    'validate_canonical_event',
    'normalize_github_push',
    'normalize_github_pull_request',
    'normalize_github_commit_comment',
    'normalize_manual_event',
    'normalize_strava_activity',
]
