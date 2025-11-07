"""
GitHub Webhooks API

Receives and processes webhook events from GitHub (push, PR, commits).
Implements signature verification for security and stores events for game mechanics.
"""
from fastapi import APIRouter, Request, HTTPException, Depends, Header
from sqlalchemy.orm import Session
from typing import Optional
import hmac
import hashlib
import uuid
from datetime import datetime

from ...core.config import settings
from ...core.dependencies import get_db
from ...models import EventRaw, Event, User, Integration
from ...services.queue import QueueService


router = APIRouter()
queue = QueueService(settings.REDIS_URL)


def verify_github_signature(payload_body: bytes, signature_header: str) -> bool:
    """
    Verify that the webhook request came from GitHub.
    
    GitHub signs each webhook with HMAC-SHA256 using your webhook secret.
    This prevents attackers from sending fake webhooks to your endpoint.
    
    Args:
        payload_body: The raw request body bytes
        signature_header: The X-Hub-Signature-256 header value
        
    Returns:
        True if signature is valid, False otherwise
        
    How it works:
        1. GitHub computes: HMAC-SHA256(webhook_secret, payload) → signature
        2. GitHub sends signature in X-Hub-Signature-256 header
        3. We compute the same: HMAC-SHA256(our_secret, payload) → our_signature
        4. We compare: if they match, it's authentic
    """
    if not signature_header:
        return False
    
    # GitHub sends signature as "sha256=<hex_digest>"
    if not signature_header.startswith("sha256="):
        return False
    
    # Extract just the hex digest part
    github_signature = signature_header[7:]  # Remove "sha256=" prefix
    
    # Compute what the signature should be
    secret_bytes = settings.GITHUB_WEBHOOK_SECRET.encode('utf-8')
    computed_hmac = hmac.new(secret_bytes, payload_body, hashlib.sha256)
    expected_signature = computed_hmac.hexdigest()
    
    # Use constant-time comparison to prevent timing attacks
    # hmac.compare_digest ensures the comparison takes the same time
    # regardless of where strings differ (security best practice)
    return hmac.compare_digest(expected_signature, github_signature)


async def process_push_event(payload: dict, db: Session, event_raw_id: uuid.UUID) -> list[Event]:
    """
    Process a GitHub push event.
    
    A push event contains one or more commits that were pushed to a repository.
    We create one Event record per commit for game mechanics.
    
    Args:
        payload: The GitHub push event payload
        db: Database session
        event_raw_id: ID of the EventRaw record
        
    Returns:
        List of created Event objects
    """
    events = []
    
    # Get the GitHub user who pushed
    sender = payload.get('sender', {})
    github_user_id = str(sender.get('id'))
    
    # Find our user by their GitHub ID
    user = db.query(User).filter(User.github_id == github_user_id).first()
    if not user:
        # User not found - they might not have connected GitHub to our app
        return events
    
    # Get repository info for context
    repo = payload.get('repository', {})
    repo_name = repo.get('full_name', 'unknown')
    
    # Process each commit in the push
    commits = payload.get('commits', [])
    for commit in commits:
        event = Event(
            id=uuid.uuid4(),
            event_raw_id=event_raw_id,
            user_id=user.id,
            pet_id=None,  # Will be assigned by game logic later
            type='github_commit',
            value=1.0,  # Same scoring for now
            meta={
                'commit_sha': commit.get('id'),
                'message': commit.get('message'),
                'url': commit.get('url'),
                'repository': repo_name,
                'branch': payload.get('ref', '').replace('refs/heads/', ''),
                'timestamp': commit.get('timestamp'),
            },
            scored=False  # Will be scored by game engine
        )
        db.add(event)
        events.append(event)
    
    return events


async def process_pull_request_event(payload: dict, db: Session, event_raw_id: uuid.UUID) -> list[Event]:
    """
    Process a GitHub pull request event.
    
    Triggered when a PR is opened, closed, merged, etc.
    We track PR creation and merges for game mechanics.
    
    Args:
        payload: The GitHub PR event payload
        db: Database session
        event_raw_id: ID of the EventRaw record
        
    Returns:
        List of created Event objects
    """
    events = []
    
    # Get action (opened, closed, merged, etc.)
    action = payload.get('action')
    
    # We only care about certain actions
    if action not in ['opened', 'closed']:
        return events
    
    # Get the GitHub user
    sender = payload.get('sender', {})
    github_user_id = str(sender.get('id'))
    
    user = db.query(User).filter(User.github_id == github_user_id).first()
    if not user:
        return events
    
    # Get PR details
    pull_request = payload.get('pull_request', {})
    pr_number = pull_request.get('number')
    pr_title = pull_request.get('title')
    merged = pull_request.get('merged', False)
    
    repo = payload.get('repository', {})
    repo_name = repo.get('full_name', 'unknown')
    
    # Determine event type based on action and merge status
    if action == 'opened':
        event_type = 'github_pr_opened'
    elif action == 'closed' and merged:
        event_type = 'github_pr_merged'
    else:
        # Closed but not merged (just closed)
        event_type = 'github_pr_closed'
    
    event = Event(
        id=uuid.uuid4(),
        event_raw_id=event_raw_id,
        user_id=user.id,
        pet_id=None,
        type=event_type,
        value=1.0,  # Same scoring for now
        meta={
            'pr_number': pr_number,
            'title': pr_title,
            'url': pull_request.get('html_url'),
            'repository': repo_name,
            'merged': merged,
            'action': action,
        },
        scored=False
    )
    db.add(event)
    events.append(event)
    
    return events


async def process_commit_comment_event(payload: dict, db: Session, event_raw_id: uuid.UUID) -> list[Event]:
    """
    Process a GitHub commit comment event.
    
    Triggered when someone comments on a specific commit.
    Tracks code review engagement.
    
    Args:
        payload: The GitHub commit comment event payload
        db: Database session
        event_raw_id: ID of the EventRaw record
        
    Returns:
        List of created Event objects
    """
    events = []
    
    # Get the GitHub user who commented
    sender = payload.get('sender', {})
    github_user_id = str(sender.get('id'))
    
    user = db.query(User).filter(User.github_id == github_user_id).first()
    if not user:
        return events
    
    # Get comment details
    comment = payload.get('comment', {})
    commit_id = comment.get('commit_id')
    comment_body = comment.get('body', '')
    
    repo = payload.get('repository', {})
    repo_name = repo.get('full_name', 'unknown')
    
    event = Event(
        id=uuid.uuid4(),
        event_raw_id=event_raw_id,
        user_id=user.id,
        pet_id=None,
        type='github_commit_comment',
        value=1.0,  # Same scoring for now
        meta={
            'commit_sha': commit_id,
            'comment_body': comment_body[:500],  # Truncate to 500 chars
            'url': comment.get('html_url'),
            'repository': repo_name,
        },
        scored=False
    )
    db.add(event)
    events.append(event)
    
    return events


@router.post("/webhooks/github")
async def receive_github_webhook(
    request: Request,
    db: Session = Depends(get_db),
    x_github_event: Optional[str] = Header(None, alias="X-GitHub-Event"),
    x_github_delivery: Optional[str] = Header(None, alias="X-GitHub-Delivery"),
    x_hub_signature_256: Optional[str] = Header(None, alias="X-Hub-Signature-256"),
):
    """
    GitHub Webhook Receiver Endpoint
    
    This endpoint receives webhook events from GitHub and queues them for async processing.
    Returns immediately after storing the raw event and publishing to Redis queue.
    
    Security:
        - Verifies HMAC-SHA256 signature to ensure request is from GitHub
        - Rejects requests with invalid signatures
        
    Process Flow:
        1. Verify webhook signature (security)
        2. Parse event type from header
        3. Store raw payload in EventRaw table (idempotency, audit trail)
        4. Publish event to Redis queue for background processing
        5. Return success response immediately (fast response)
        6. Worker processes event asynchronously
        
    Idempotency:
        - Uses X-GitHub-Delivery header as external_event_id
        - Duplicate webhooks (GitHub retries) are detected and handled
        
    Supported Events:
        - push: Code pushed to repository
        - pull_request: PR opened/closed/merged
        - commit_comment: Comment on a commit
        
    Returns:
        200: Event queued successfully or duplicate detected
        401: Invalid signature
        400: Missing required headers or invalid payload
    """
    # Read the raw request body for signature verification
    body = await request.body()
    
    # Step 1: Verify signature (SECURITY CRITICAL)
    if not verify_github_signature(body, x_hub_signature_256):
        raise HTTPException(
            status_code=401,
            detail="Invalid webhook signature. Ensure your webhook secret matches."
        )
    
    # Step 2: Check required headers
    if not x_github_event:
        raise HTTPException(
            status_code=400,
            detail="Missing X-GitHub-Event header"
        )
    
    if not x_github_delivery:
        raise HTTPException(
            status_code=400,
            detail="Missing X-GitHub-Delivery header"
        )
    
    # Step 3: Parse JSON payload
    try:
        payload = await request.json()
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid JSON payload: {str(e)}"
        )
    
    # Step 4: Check for duplicate webhook (idempotency)
    # GitHub may resend webhooks if they don't get a timely response
    existing_event = db.query(EventRaw).filter(
        EventRaw.external_event_id == x_github_delivery
    ).first()
    
    if existing_event:
        # Already processed this webhook delivery
        return {
            "status": "duplicate",
            "message": "Webhook already processed",
            "event_raw_id": str(existing_event.id)
        }
    
    # Step 5: Store raw event in database
    # This gives us an audit trail and allows reprocessing if needed
    event_raw = EventRaw(
        id=uuid.uuid4(),
        integration_id=None,  # Will link to integration when we find the user
        external_event_id=x_github_delivery,
        payload=payload,
        processed=False  # Will be marked True after processing
    )
    db.add(event_raw)
    db.flush()  # Get the ID without committing yet
    
    
    try:
        # Publish to webhook-events stream with integration_source
        if x_github_event in ['push', 'pull_request', 'commit_comment']:
            queue.publish('webhook-events', {
                'event_raw_id': str(event_raw.id),
                'event_type': f'github.{x_github_event}',
                'integration_source': 'github'  # NEW: For goal matching
            })
        else:
            # Unsupported event type - just store the raw event
            pass
        

        

        # Commit all changes
        db.commit()
        
        return {
            "status": "success",
            "event_type": x_github_event,
            "delivery_id": x_github_delivery,
            "event_raw_id": str(event_raw.id),
            "message": "Event queued for processing"
        }
        
    except Exception as e:
        # If processing fails, rollback but keep the raw event for debugging
        db.rollback()
        
        # Re-add just the raw event
        event_raw.processed = False
        db.add(event_raw)
        db.commit()
        
        # Return error but with 200 status so GitHub doesn't retry
        # (We've saved the raw event for manual review)
        return {
            "status": "error",
            "event_type": x_github_event,
            "delivery_id": x_github_delivery,
            "error": str(e),
            "event_raw_id": str(event_raw.id),
            "message": "Raw event saved for manual processing"
        }


@router.get("/webhooks/github/health")
async def webhook_health():
    """
    Health check endpoint for webhook receiver.
    Use this to verify your webhook endpoint is accessible from GitHub.
    """
    return {
        "status": "healthy",
        "endpoint": "/webhooks/github",
        "supported_events": ["push", "pull_request", "commit_comment"]
    }
