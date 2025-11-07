from sqlalchemy import select
from fastapi import APIRouter, Request, HTTPException, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import hmac
import hashlib
import uuid
from datetime import datetime

from ...core.config import settings
from ...core.dependencies import get_db
from ...models import EventRaw, Integration
from ...services.queue import get_redis_client


router = APIRouter()


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


@router.post("/webhooks/github")
async def receive_github_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
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
    result = await db.execute(select(EventRaw).filter(EventRaw.external_event_id == x_github_delivery))
    existing_event = result.scalar_one_or_none()
    
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
    await db.flush()  # Get the ID without committing yet
    
    # Get queue service
    queue_service = get_redis_client()
    
    try:
        # Publish to webhook-events stream with integration_source
        if x_github_event in ['push', 'pull_request', 'commit_comment']:
            await queue_service.publish('webhook-events', {
                'event_raw_id': str(event_raw.id),
                'event_type': f'github.{x_github_event}',
                'integration_source': 'github'  # For goal matching
            })
        else:
            # Unsupported event type - just store the raw event
            pass

        # Commit all changes
        await db.commit()
        
        return {
            "status": "success",
            "event_type": x_github_event,
            "delivery_id": x_github_delivery,
            "event_raw_id": str(event_raw.id),
            "message": "Event queued for processing"
        }
        
    except Exception as e:
        # If processing fails, rollback but keep the raw event for debugging
        await db.rollback()
        
        # Re-add just the raw event
        event_raw.processed = False
        db.add(event_raw)
        await db.commit()
        
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
