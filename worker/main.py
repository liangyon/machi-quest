"""
GitHub Webhook Worker

Consumes webhook events from Redis queue and processes them asynchronously.
This separates the webhook receiver (fast response) from event processing (slow work).
"""
import os
import sys
import time
import logging
from uuid import UUID

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../backend'))

from app.core.config import settings
from app.services.queue import QueueService
from app.db.database import SessionLocal
from app.db.models import EventRaw, Integration
from app.api.github_webhooks import (
    process_push_event,
    process_pull_request_event,
    process_commit_comment_event
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
STREAM_NAME = 'webhook-events'
GROUP_NAME = 'workers'
CONSUMER_NAME = 'worker-1'


def process_message(queue: QueueService, msg_id: str, data: dict):
    """
    Process a single webhook event message.
    
    Args:
        queue: QueueService instance
        msg_id: Redis message ID
        data: Message payload containing event_raw_id and event_type
    """
    db = SessionLocal()
    
    try:
        event_raw_id = data.get('event_raw_id')
        event_type = data.get('event_type')
        
        if not event_raw_id:
            logger.error(f"Message {msg_id} missing event_raw_id")
            queue.acknowledge(STREAM_NAME, GROUP_NAME, msg_id)
            return
        
        logger.info(f"Processing {event_type} event: {event_raw_id}")
        
        # Load EventRaw from database
        event_raw = db.query(EventRaw).filter(
            EventRaw.id == UUID(event_raw_id)
        ).first()
        
        if not event_raw:
            logger.error(f"EventRaw {event_raw_id} not found in database")
            queue.acknowledge(STREAM_NAME, GROUP_NAME, msg_id)
            return
        
        # Check if already processed (shouldn't happen but safety check)
        if event_raw.processed:
            logger.warning(f"EventRaw {event_raw_id} already processed, skipping")
            queue.acknowledge(STREAM_NAME, GROUP_NAME, msg_id)
            return
        
        # Process based on event type
        created_events = []
        
        if event_type == 'push':
            # Synchronous call (remove await since we're not in async context)
            import asyncio
            created_events = asyncio.run(
                process_push_event(event_raw.payload, db, event_raw.id)
            )
        elif event_type == 'pull_request':
            import asyncio
            created_events = asyncio.run(
                process_pull_request_event(event_raw.payload, db, event_raw.id)
            )
        elif event_type == 'commit_comment':
            import asyncio
            created_events = asyncio.run(
                process_commit_comment_event(event_raw.payload, db, event_raw.id)
            )
        else:
            logger.warning(f"Unknown event type: {event_type}")
        
        # Link EventRaw to user's integration if events were created
        if created_events and len(created_events) > 0:
            user_id = created_events[0].user_id
            integration = db.query(Integration).filter(
                Integration.user_id == user_id,
                Integration.provider == 'github'
            ).first()
            if integration:
                event_raw.integration_id = integration.id
        
        # Mark as processed
        event_raw.processed = True
        db.commit()
        
        # Acknowledge message (remove from queue)
        queue.acknowledge(STREAM_NAME, GROUP_NAME, msg_id)
        
        logger.info(
            f"Successfully processed {event_type} event {event_raw_id}, "
            f"created {len(created_events)} Event records"
        )
        
    except Exception as e:
        logger.error(f"Error processing message {msg_id}: {e}", exc_info=True)
        db.rollback()
        # Don't ACK on error - message stays in pending for retry
        # You could add logic here to move to dead letter queue after X retries
        
    finally:
        db.close()


def main():
    """
    Main worker loop.
    
    Continuously reads messages from Redis queue and processes them.
    Handles errors gracefully and keeps running.
    """
    logger.info(f"Starting webhook worker: {CONSUMER_NAME}")
    logger.info(f"Redis URL: {settings.REDIS_URL}")
    logger.info(f"Listening to stream: {STREAM_NAME}")
    
    queue = QueueService(settings.REDIS_URL)
    
    # Ensure consumer group exists
    try:
        queue.ensure_consumer_group(STREAM_NAME, GROUP_NAME)
        logger.info(f"Consumer group '{GROUP_NAME}' ready")
    except Exception as e:
        logger.error(f"Failed to create consumer group: {e}")
        raise
    
    logger.info("Worker started successfully, waiting for messages...")
    
    # Main processing loop
    while True:
        try:
            # Read messages from queue
            # count=10: Process up to 10 messages at once
            # block=5000: Wait up to 5 seconds for new messages
            for msg_id, data in queue.consume(
                STREAM_NAME, 
                GROUP_NAME, 
                CONSUMER_NAME,
                count=10,
                block=5000
            ):
                process_message(queue, msg_id, data)
                
        except KeyboardInterrupt:
            logger.info("Received shutdown signal, stopping worker...")
            break
            
        except Exception as e:
            logger.error(f"Error in main loop: {e}", exc_info=True)
            # Wait a bit before retrying to avoid rapid error loops
            time.sleep(5)
    
    logger.info("Worker stopped")


if __name__ == "__main__":
    main()
