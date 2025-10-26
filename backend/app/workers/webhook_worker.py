"""
GitHub Webhook Worker

Consumes webhook events from Redis queue and processes them asynchronously.
This worker runs as a separate process but uses the same codebase as the API.

Features:
- Clean imports (no path hacks)
- Pending message recovery (handles crashes)
- Graceful error handling
- Continuous processing loop
"""
import time
import logging
from uuid import UUID
import asyncio

from app.services.queue import QueueService
from app.core.config import settings
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
            created_events = asyncio.run(
                process_push_event(event_raw.payload, db, event_raw.id)
            )
        elif event_type == 'pull_request':
            created_events = asyncio.run(
                process_pull_request_event(event_raw.payload, db, event_raw.id)
            )
        elif event_type == 'commit_comment':
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
        
    finally:
        db.close()


def recover_pending_messages(queue: QueueService):
    """
    Process any pending messages from previous crashes.
    
    When a worker crashes, messages it was processing stay in "pending" state.
    This function recovers and reprocesses those messages.
    
    Called once on worker startup before processing new messages.
    """
    logger.info("Checking for pending messages from previous crashes...")
    
    try:
        # Read pending messages using '0' instead of '>'
        # '0' = give me messages that were delivered but not ACK'd
        pending_count = 0
        
        for msg_id, data in queue.consume(
            STREAM_NAME,
            GROUP_NAME,
            CONSUMER_NAME,
            count=100,  # Process up to 100 pending at once
            block=1000   # Don't wait long, just check once
        ):
            logger.info(f"Recovering pending message: {msg_id}")
            process_message(queue, msg_id, data)
            pending_count += 1
        
        if pending_count > 0:
            logger.info(f"Recovered {pending_count} pending messages")
        else:
            logger.info("No pending messages found")
            
    except Exception as e:
        logger.error(f"Error during pending message recovery: {e}", exc_info=True)


def main():
    """
    Main worker loop.
    
    Process flow:
    1. Connect to Redis
    2. Create consumer group (if not exists)
    3. Recover any pending messages (from previous crashes)
    4. Loop forever processing new messages
    5. Handle errors gracefully
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
    
    # Recover pending messages from crashes
    recover_pending_messages(queue)
    
    logger.info("Worker started successfully, waiting for new messages...")
    
    # Main processing loop
    while True:
        try:
            # Read NEW messages from queue
            # count=10: Process up to 10 messages at once (batch processing)
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
