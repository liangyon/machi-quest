"""
Event Extractors - Lightweight value extraction from webhook payloads

These functions extract the amount to increment goal progress by,
replacing the old complex normalizer system.

The old system created CanonicalEvent objects for scoring engine.
The new system just needs to know: "What number should we increment by?"
"""
from typing import Dict, Any, Optional


def extract_github_amount(event_type: str, payload: Dict[str, Any]) -> int:
    """
    Extract increment amount from GitHub webhook payload.
    
    Args:
        event_type: Type of GitHub event (e.g., 'github.push', 'github.pull_request')
        payload: GitHub webhook payload
        
    Returns:
        Amount to increment goal progress by
        
    Examples:
        - Push with 5 commits → returns 5 (for "daily commits" goals)
        - PR opened → returns 1 (for "weekly PRs" goals)
        - PR merged → returns 1 (for "merged PRs" goals)
    """
    if 'push' in event_type:
        # For push events, count number of commits
        commits = payload.get('commits', [])
        return len(commits) if commits else 1
    
    elif 'pull_request' in event_type:
        # For PRs, it's binary (1 PR = 1 count)
        return 1
    
    elif 'commit_comment' in event_type:
        # For comments, it's binary (1 comment = 1 count)
        return 1
    
    # Default to 1 for unknown event types
    return 1


def extract_strava_amount(event_type: str, payload: Dict[str, Any], unit: str = 'count') -> float:
    """
    Extract increment amount from Strava webhook payload.
    
    Args:
        event_type: Type of Strava event (e.g., 'strava.activity')
        payload: Strava webhook/activity payload
        unit: The unit to extract (km, minutes, count, etc.)
        
    Returns:
        Amount to increment goal progress by
        
    Examples:
        - Run 10km, unit='km' → returns 10.0
        - Workout 45min, unit='minutes' → returns 45.0
        - Any activity, unit='count' → returns 1.0
        
    Note:
        In production, you'd fetch full activity details from Strava API.
        The webhook payload doesn't include distance/duration, only activity ID.
        For now, this returns 1 until we implement the API fetch.
    """
    # TODO: Fetch activity details from Strava API using activity ID
    # For now, we only have the webhook payload which doesn't include details
    # In production, add: activity_details = fetch_strava_activity(payload['object_id'])
    
    if unit == 'km' or unit == 'kilometers':
        # Distance in meters, convert to km
        # TODO: Get from activity_details['distance'] / 1000
        return payload.get('distance', 0) / 1000 if 'distance' in payload else 1.0
    
    elif unit == 'minutes' or unit == 'time':
        # Duration in seconds, convert to minutes
        # TODO: Get from activity_details['moving_time'] / 60
        return payload.get('moving_time', 0) / 60 if 'moving_time' in payload else 1.0
    
    elif unit == 'count' or unit == 'activities':
        # Binary: 1 activity = 1 count
        return 1.0
    
    # Default to 1 for unknown units
    return 1.0


def extract_amount(
    integration_source: str,
    event_type: str,
    payload: Dict[str, Any],
    unit: Optional[str] = None
) -> float:
    """
    Main extraction function - routes to the appropriate extractor.
    
    Args:
        integration_source: Source of the event ('github', 'strava', 'manual')
        event_type: Type of event (e.g., 'github.push', 'strava.activity')
        payload: Event payload
        unit: The unit to extract (optional, used for Strava)
        
    Returns:
        Amount to increment goal progress by
        
    Usage:
        amount = extract_amount('github', 'github.push', github_payload)
        # Returns number of commits
        
        amount = extract_amount('strava', 'strava.activity', strava_payload, unit='km')
        # Returns distance in km
    """
    if integration_source == 'github':
        return float(extract_github_amount(event_type, payload))
    
    elif integration_source == 'strava':
        return extract_strava_amount(event_type, payload, unit or 'count')
    
    elif integration_source == 'manual':
        # Manual events should specify the amount explicitly
        return float(payload.get('amount', 1.0))
    
    # Default to 1 for unknown sources
    return 1.0
