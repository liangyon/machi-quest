"""
Admin/Debug API endpoints

Provides administrative and debugging endpoints for viewing raw webhook events,
monitoring system health, and troubleshooting integration issues.
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from datetime import datetime

from ..core.dependencies import get_db
from ..models import EventRaw, Event, Integration, User


router = APIRouter()


@router.get("/webhooks/raw")
async def list_raw_webhooks(
    limit: int = Query(20, ge=1, le=100, description="Number of events to return"),
    offset: int = Query(0, ge=0, description="Number of events to skip"),
    processed: Optional[bool] = Query(None, description="Filter by processed status"),
    integration_id: Optional[str] = Query(None, description="Filter by integration ID"),
    db: Session = Depends(get_db)
):
    """
    List raw webhook events with their payloads.
    
    This endpoint is useful for:
    - Debugging webhook delivery issues
    - Verifying webhook payloads are being received
    - Troubleshooting event processing errors
    - Auditing webhook history
    
    Query Parameters:
        limit: Number of events to return (1-100, default: 20)
        offset: Number of events to skip for pagination (default: 0)
        processed: Filter by processed status (true/false)
        integration_id: Filter by specific integration UUID
        
    Returns:
        JSON object with:
        - total: Total count of matching events
        - limit: Current limit
        - offset: Current offset
        - events: List of raw webhook events with full payloads
        
    Example:
        GET /admin/webhooks/raw?limit=10&processed=false
        
    Security Note:
        This endpoint exposes sensitive data including full webhook payloads.
        In production, this should require authentication and admin privileges.
    """
    # Build base query
    query = db.query(EventRaw)
    
    # Apply filters
    if processed is not None:
        query = query.filter(EventRaw.processed == processed)
    
    if integration_id:
        try:
            query = query.filter(EventRaw.integration_id == integration_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid integration_id format")
    
    # Get total count
    total = query.count()
    
    # Order by newest first and apply pagination
    events_raw = query.order_by(EventRaw.received_at.desc()).offset(offset).limit(limit).all()
    
    # Format response
    events_list = []
    for event_raw in events_raw:
        # Count how many Event records were created from this raw event
        events_created = db.query(func.count(Event.id)).filter(
            Event.event_raw_id == event_raw.id
        ).scalar()
        
        # Get integration info if available
        integration_info = None
        if event_raw.integration_id:
            integration = db.query(Integration).filter(
                Integration.id == event_raw.integration_id
            ).first()
            if integration:
                integration_info = {
                    "id": str(integration.id),
                    "provider": integration.provider,
                    "user_id": str(integration.user_id)
                }
        
        events_list.append({
            "id": str(event_raw.id),
            "integration_id": str(event_raw.integration_id) if event_raw.integration_id else None,
            "integration": integration_info,
            "external_event_id": event_raw.external_event_id,
            "processed": event_raw.processed,
            "received_at": event_raw.received_at.isoformat() if event_raw.received_at else None,
            "payload": event_raw.payload,
            "events_created": events_created
        })
    
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "count": len(events_list),
        "events": events_list
    }


@router.get("/webhooks/raw/{event_raw_id}")
async def get_raw_webhook_by_id(
    event_raw_id: str,
    db: Session = Depends(get_db)
):
    """
    Get a single raw webhook event by ID with detailed information.
    
    Includes:
    - Full raw payload
    - Processing status
    - Associated Event records created
    - Integration and user information
    
    Args:
        event_raw_id: UUID of the EventRaw record
        
    Returns:
        Detailed information about the raw webhook event
        
    Example:
        GET /admin/webhooks/raw/123e4567-e89b-12d3-a456-426614174000
    """
    try:
        event_raw = db.query(EventRaw).filter(EventRaw.id == event_raw_id).first()
        
        if not event_raw:
            raise HTTPException(status_code=404, detail="Raw webhook event not found")
        
        # Get all Event records created from this raw event
        events = db.query(Event).filter(Event.event_raw_id == event_raw.id).all()
        
        events_list = []
        for event in events:
            events_list.append({
                "id": str(event.id),
                "user_id": str(event.user_id),
                "goal_id": str(event.goal_id) if event.goal_id else None,
                "type": event.type,
                "value": event.value,
                "meta": event.meta,
                "scored": event.scored,
                "created_at": event.created_at.isoformat() if event.created_at else None
            })
        
        # Get integration info
        integration_info = None
        user_info = None
        if event_raw.integration_id:
            integration = db.query(Integration).filter(
                Integration.id == event_raw.integration_id
            ).first()
            if integration:
                integration_info = {
                    "id": str(integration.id),
                    "provider": integration.provider,
                    "created_at": integration.created_at.isoformat() if integration.created_at else None
                }
                
                # Get user info
                user = db.query(User).filter(User.id == integration.user_id).first()
                if user:
                    user_info = {
                        "id": str(user.id),
                        "email": user.email,
                        "display_name": user.display_name,
                        "github_username": user.github_username
                    }
        
        return {
            "id": str(event_raw.id),
            "integration_id": str(event_raw.integration_id) if event_raw.integration_id else None,
            "integration": integration_info,
            "user": user_info,
            "external_event_id": event_raw.external_event_id,
            "processed": event_raw.processed,
            "received_at": event_raw.received_at.isoformat() if event_raw.received_at else None,
            "payload": event_raw.payload,
            "events_created": len(events_list),
            "events": events_list
        }
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid event_raw_id format")


@router.get("/webhooks/stats")
async def get_webhook_stats(db: Session = Depends(get_db)):
    """
    Get statistics about webhook processing.
    
    Provides overview metrics including:
    - Total webhooks received
    - Processed vs unprocessed count
    - Events created from webhooks
    - Recent activity
    
    Returns:
        Statistics object with webhook processing metrics
        
    Example:
        GET /admin/webhooks/stats
    """
    # Total raw events
    total_raw = db.query(func.count(EventRaw.id)).scalar()
    
    # Processed vs unprocessed
    processed_count = db.query(func.count(EventRaw.id)).filter(
        EventRaw.processed == True
    ).scalar()
    unprocessed_count = total_raw - processed_count
    
    # Total events created
    total_events = db.query(func.count(Event.id)).scalar()
    
    # Events by type
    events_by_type = db.query(
        Event.type,
        func.count(Event.id).label('count')
    ).group_by(Event.type).all()
    
    event_types = {event_type: count for event_type, count in events_by_type}
    
    # Recent activity (last 24 hours)
    from datetime import timedelta
    yesterday = datetime.utcnow() - timedelta(days=1)
    recent_raw = db.query(func.count(EventRaw.id)).filter(
        EventRaw.received_at >= yesterday
    ).scalar()
    
    recent_events = db.query(func.count(Event.id)).filter(
        Event.created_at >= yesterday
    ).scalar()
    
    return {
        "webhooks": {
            "total": total_raw,
            "processed": processed_count,
            "unprocessed": unprocessed_count,
            "recent_24h": recent_raw
        },
        "events": {
            "total": total_events,
            "recent_24h": recent_events,
            "by_type": event_types
        },
        "processing_rate": f"{(processed_count / total_raw * 100):.1f}%" if total_raw > 0 else "N/A"
    }


@router.get("/health")
async def admin_health():
    """
    Admin health check endpoint.
    
    Returns:
        Status indicating the admin API is operational
    """
    return {
        "status": "healthy",
        "service": "admin-api",
        "endpoints": [
            "/admin/webhooks/raw",
            "/admin/webhooks/raw/{id}",
            "/admin/webhooks/stats",
            "/admin/health"
        ]
    }
