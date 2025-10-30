"""
Strava Event Normalizers

Transforms Strava webhook payloads into canonical events.
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from ..event_normalizer import CanonicalEvent, EventType


def normalize_strava_activity(
    payload: dict,
    user_id: UUID,
    event_raw_id: Optional[UUID] = None
) -> List[CanonicalEvent]:
    """
    Normalize a Strava activity event.
    
    Strava webhook payload example:
    {
        "object_type": "activity",
        "object_id": 12345,
        "aspect_type": "create",
        "updates": {},
        "owner_id": 67890
    }
    
    Then you fetch activity details from Strava API:
    {
        "id": 12345,
        "name": "Morning Run",
        "type": "Run",
        "distance": 5210.3,  # meters
        "moving_time": 1680,  # seconds (28 minutes)
        "elapsed_time": 1800,
        "start_date": "2025-10-29T06:00:00Z",
        "achievement_count": 2,
        "kudos_count": 5
    }
    """
    events = []
    
    # Extract activity details
    activity_id = payload.get('id')
    activity_type = payload.get('type', 'workout')  # Run, Ride, Swim, etc.
    distance_m = payload.get('distance', 0)
    duration_min = payload.get('moving_time', 0) / 60
    
    # Parse timestamp
    start_date = payload.get('start_date', '')
    try:
        timestamp = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
    except (ValueError, AttributeError):
        timestamp = datetime.utcnow()
    
    # Determine base value based on activity type and duration
    # Longer/harder activities = more points
    base_value = 1.0
    
    # Bonus for distance (every 5km = +1 point)
    if distance_m > 0:
        base_value += (distance_m / 5000)
    
    # Bonus for duration (every 30min = +1 point)
    if duration_min > 0:
        base_value += (duration_min / 30)
    
    event = CanonicalEvent(
        type=EventType.STRAVA_ACTIVITY,
        timestamp=timestamp,
        user_id=user_id,
        value=base_value,
        meta={
            'activity_id': activity_id,
            'activity_type': activity_type.lower(),
            'distance_km': round(distance_m / 1000, 2),
            'duration_minutes': round(duration_min, 1),
            'elevation_gain_m': payload.get('total_elevation_gain', 0),
            'kudos_count': payload.get('kudos_count', 0),
            'source': 'strava',
        },
        event_raw_id=event_raw_id
    )
    events.append(event)
    
    return events