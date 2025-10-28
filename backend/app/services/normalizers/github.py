"""
GitHub Event Normalizers

Transforms GitHub webhook payloads into canonical events.
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from ..event_normalizer import CanonicalEvent, EventType


def normalize_github_push(
    payload: dict,
    user_id: UUID,
    event_raw_id: Optional[UUID] = None
) -> List[CanonicalEvent]:
    """
    Normalize a GitHub push event into canonical events.
    
    A push can contain multiple commits, so we create one CanonicalEvent
    per commit. This allows fine-grained scoring (each commit = points).
    
    Args:
        payload: GitHub push webhook payload
        user_id: UUID of the user who pushed
        event_raw_id: Optional link to EventRaw record
        
    Returns:
        List of CanonicalEvent objects (one per commit)
        
    Example payload structure:
        {
            "commits": [
                {
                    "id": "abc123...",
                    "message": "Fix bug",
                    "timestamp": "2025-10-27T14:30:00Z",
                    "url": "https://github.com/..."
                }
            ],
            "repository": {"full_name": "user/repo"},
            "ref": "refs/heads/main"
        }
    """
    events = []
    
    # Extract repository context
    repo = payload.get('repository', {})
    repo_name = repo.get('full_name', 'unknown')
    branch = payload.get('ref', '').replace('refs/heads/', '')
    
    # Process each commit
    commits = payload.get('commits', [])
    for commit in commits:
        # Parse ISO timestamp from GitHub
        timestamp_str = commit.get('timestamp', '')
        try:
            # GitHub timestamps are in ISO format with 'Z' suffix
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            # Fallback to current time if parsing fails
            timestamp = datetime.utcnow()
        
        event = CanonicalEvent(
            type=EventType.GITHUB_COMMIT,
            timestamp=timestamp,
            user_id=user_id,
            value=1.0,  # Each commit = 1 point (scoring engine may adjust)
            meta={
                'commit_sha': commit.get('id', ''),
                'message': commit.get('message', '')[:500],  # Truncate long messages
                'url': commit.get('url', ''),
                'repository': repo_name,
                'branch': branch,
                'source': 'github',
            },
            event_raw_id=event_raw_id
        )
        events.append(event)
    
    return events


def normalize_github_pull_request(
    payload: dict,
    user_id: UUID,
    event_raw_id: Optional[UUID] = None
) -> List[CanonicalEvent]:
    """
    Normalize a GitHub pull request event into canonical events.
    
    Handles PR actions: opened, closed (merged or not).
    
    Args:
        payload: GitHub pull_request webhook payload
        user_id: UUID of the user
        event_raw_id: Optional link to EventRaw record
        
    Returns:
        List containing 0 or 1 CanonicalEvent (depending on action)
        
    Example payload structure:
        {
            "action": "opened",  # or "closed"
            "pull_request": {
                "number": 42,
                "title": "Add feature",
                "html_url": "https://github.com/...",
                "merged": true,  # only present on 'closed' action
                "created_at": "2025-10-27T14:30:00Z"
            },
            "repository": {"full_name": "user/repo"}
        }
    """
    events = []
    
    action = payload.get('action')
    
    # Only process certain actions
    if action not in ['opened', 'closed']:
        return events
    
    pull_request = payload.get('pull_request', {})
    pr_number = pull_request.get('number')
    pr_title = pull_request.get('title', '')
    merged = pull_request.get('merged', False)
    
    repo = payload.get('repository', {})
    repo_name = repo.get('full_name', 'unknown')
    
    # Determine event type based on action
    if action == 'opened':
        event_type = EventType.GITHUB_PR_OPENED
    elif action == 'closed' and merged:
        event_type = EventType.GITHUB_PR_MERGED
    else:
        # Closed but not merged
        event_type = EventType.GITHUB_PR_CLOSED
    
    # Parse timestamp
    timestamp_str = pull_request.get('created_at', '')
    try:
        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
    except (ValueError, AttributeError):
        timestamp = datetime.utcnow()
    
    event = CanonicalEvent(
        type=event_type,
        timestamp=timestamp,
        user_id=user_id,
        value=1.0,
        meta={
            'pr_number': pr_number,
            'title': pr_title[:500],  # Truncate long titles
            'url': pull_request.get('html_url', ''),
            'repository': repo_name,
            'merged': merged,
            'action': action,
            'source': 'github',
        },
        event_raw_id=event_raw_id
    )
    events.append(event)
    
    return events


def normalize_github_commit_comment(
    payload: dict,
    user_id: UUID,
    event_raw_id: Optional[UUID] = None
) -> List[CanonicalEvent]:
    """
    Normalize a GitHub commit comment event into canonical events.
    
    Triggered when someone comments on a specific commit.
    
    Args:
        payload: GitHub commit_comment webhook payload
        user_id: UUID of the user who commented
        event_raw_id: Optional link to EventRaw record
        
    Returns:
        List containing 1 CanonicalEvent
        
    Example payload structure:
        {
            "comment": {
                "commit_id": "abc123",
                "body": "Great work!",
                "html_url": "https://github.com/...",
                "created_at": "2025-10-27T14:30:00Z"
            },
            "repository": {"full_name": "user/repo"}
        }
    """
    events = []
    
    comment = payload.get('comment', {})
    commit_id = comment.get('commit_id', '')
    comment_body = comment.get('body', '')
    
    repo = payload.get('repository', {})
    repo_name = repo.get('full_name', 'unknown')
    
    # Parse timestamp
    timestamp_str = comment.get('created_at', '')
    try:
        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
    except (ValueError, AttributeError):
        timestamp = datetime.utcnow()
    
    event = CanonicalEvent(
        type=EventType.GITHUB_COMMIT_COMMENT,
        timestamp=timestamp,
        user_id=user_id,
        value=1.0,
        meta={
            'commit_sha': commit_id,
            'comment_body': comment_body[:500],  # Truncate long comments
            'url': comment.get('html_url', ''),
            'repository': repo_name,
            'source': 'github',
        },
        event_raw_id=event_raw_id
    )
    events.append(event)
    
    return events
