"""
Strava Webhooks API

Receives and processes webhook events from Strava.
Similar structure to GitHub webhooks.
"""
from fastapi import APIRouter, Request, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
import uuid

from ...core.config import settings
from ...core.dependencies import get_db
from ...models import EventRaw, User, Integration
from ...services.queue import QueueService, WEBHOOK_EVENTS_STREAM

router = APIRouter()
queue = QueueService(settings.REDIS_URL)


@router.get("/webhooks/strava")
async def strava_webhook_validation(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token")
):
    """
    Strava webhook validation endpoint.
    
    Strava sends a GET request to verify your webhook endpoint.
    You must return the challenge value to confirm subscription.
    
    Docs: https://developers.strava.com/docs/webhooks/
    """
    if hub_mode == "subscribe":
        # Verify the token matches your config
        expected_token = settings.STRAVA_VERIFY_TOKEN or "YOUR_VERIFY_TOKEN"
        if hub_verify_token == expected_token:
            return {"hub.challenge": hub_challenge}
        else:
            raise HTTPException(status_code=403, detail="Invalid verify token")
    
    raise HTTPException(status_code=400, detail="Invalid request")


@router.post("/webhooks/strava")
async def receive_strava_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Strava Webhook Receiver Endpoint
    
    Receives activity events from Strava.
    
    Webhook payload example:
    {
        "object_type": "activity",
        "object_id": 12345,
        "aspect_type": "create",  # or "update", "delete"
        "updates": {},
        "owner_id": 67890,
        "subscription_id": 123,
        "event_time": 1234567890
    }
    
    Process flow:
    1. Parse webhook event
    2. Fetch activity details from Strava API (requires access token)
    3. Store in EventRaw
    4. Queue for processing
    """
    payload = await request.json()
    
    object_type = payload.get('object_type')
    aspect_type = payload.get('aspect_type')
    object_id = payload.get('object_id')
    owner_id = str(payload.get('owner_id'))
    
    # Only process activity creation
    if object_type != 'activity' or aspect_type != 'create':
        return {"status": "ignored", "reason": "Not an activity creation"}
    
    # Find user by Strava ID
    integration = db.query(Integration).filter(
        Integration.provider == 'strava',
        Integration.meta_data['strava_user_id'].astext == owner_id
    ).first()
    
    if not integration:
        return {"status": "ignored", "reason": "User not connected to Strava"}
    
    # Create external event ID
    external_id = f"strava-activity-{object_id}"
    
    # Check for duplicate
    existing = db.query(EventRaw).filter(
        EventRaw.external_event_id == external_id
    ).first()
    
    if existing:
        return {"status": "duplicate", "event_raw_id": str(existing.id)}
    
    # TODO: Fetch full activity details from Strava API
    # For now, store the webhook payload
    # In production, you'd call:
    # activity_details = fetch_strava_activity(object_id, integration.access_token)
    
    # Store raw event
    event_raw = EventRaw(
        id=uuid.uuid4(),
        integration_id=integration.id,
        external_event_id=external_id,
        payload=payload,  # In production, store full activity details
        processed=False
    )
    db.add(event_raw)
    db.flush()
    
    # Queue for processing
    queue.publish(WEBHOOK_EVENTS_STREAM, {
        'event_raw_id': str(event_raw.id),
        'event_type': 'strava.activity',
        'integration_source': 'strava'
    })
    
    db.commit()
    
    return {
        "status": "success",
        "event_raw_id": str(event_raw.id),
        "message": "Activity queued for processing"
    }


@router.get("/webhooks/strava/health")
async def strava_webhook_health():
    """Health check for Strava webhook endpoint."""
    return {
        "status": "healthy",
        "endpoint": "/webhooks/strava",
        "supported_events": ["activity.create"]
    }
