"""
Webhook Worker (Multi-Provider)

Consumes webhook events from Redis queue and processes them asynchronously.
Supports multiple event sources: GitHub, Strava, and more.

This worker runs as a separate process but uses the same codebase as the API.

Features:
- Multi-provider support (GitHub, Strava, etc.)
- Clean imports (no path hacks)
- Pending message recovery (handles crashes)
- Graceful error handling
- Continuous processing loop
"""
import time
import logging
from uuid import UUID
import asyncio

from app.services.queue import QueueService, WEBHOOK_EVENTS_STREAM, SCORE_DELTAS_STREAM
from app.core.config import settings
from app.db.database import SessionLocal
from app.db.models import EventRaw, Integration, Event, User, Pet
from app.services.event_normalizer import EventType
from app.services.normalizers.github import (
    normalize_github_push,
    normalize_github_pull_request,
    normalize_github_commit_comment
)
from app.services.normalizers.strava import normalize_strava_activity
from app.services.scoring_engine import ScoringEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
STREAM_NAME = WEBHOOK_EVENTS_STREAM
GROUP_NAME = 'workers'
CONSUMER_NAME = 'worker-1'

# Initialize scoring engine
scoring_engine = ScoringEngine()


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
        
        # Get user from integration (provider-agnostic approach)
        user = None
        
        if event_raw.integration_id:
            # Event already linked to integration (e.g., Strava)
            integration = db.query(Integration).filter(
                Integration.id == event_raw.integration_id
            ).first()
            if integration:
                user = db.query(User).filter(User.id == integration.user_id).first()
        else:
            # GitHub events - need to find user by GitHub ID in payload
            sender = event_raw.payload.get('sender', {})
            if sender:
                github_user_id = str(sender.get('id'))
                user = db.query(User).filter(User.github_id == github_user_id).first()
                
                # Link to integration if found
                if user:
                    integration = db.query(Integration).filter(
                        Integration.user_id == user.id,
                        Integration.provider == 'github'
                    ).first()
                    if integration:
                        event_raw.integration_id = integration.id
        
        if not user:
            logger.warning(f"User not found for event {event_raw_id}")
            event_raw.processed = True
            db.commit()
            queue.acknowledge(STREAM_NAME, GROUP_NAME, msg_id)
            return
        
        # Get user's primary pet (or create one if needed)
        pet = db.query(Pet).filter(Pet.user_id == user.id).first()
        if not pet:
            logger.info(f"Creating default pet for user {user.id}")
            pet = Pet(
                user_id=user.id,
                name="Default Pet",
                species="default",
                state_json={"food": 0, "happiness": 50, "health": 100}
            )
            db.add(pet)
            db.flush()
        
        # Step 1: Normalize to canonical events
        canonical_events = []
        if event_type == 'push':
            canonical_events = normalize_github_push(
                event_raw.payload, user.id, event_raw.id
            )
        elif event_type == 'pull_request':
            canonical_events = normalize_github_pull_request(
                event_raw.payload, user.id, event_raw.id
            )
        elif event_type == 'commit_comment':
            canonical_events = normalize_github_commit_comment(
                event_raw.payload, user.id, event_raw.id
            )
        elif event_type == 'strava_activity':
            canonical_events = normalize_strava_activity(
            event_raw.payload, user.id, event_raw.id
            )
        else:
            logger.warning(f"Unknown event type: {event_type}")
        
        # Step 2: Create Event DB records from canonical events
        created_events = []
        for canon in canonical_events:
            event = Event(
                id=UUID(str(canon.event_raw_id)) if canon.event_raw_id else UUID(str(event_raw.id)),
                event_raw_id=event_raw.id,
                user_id=canon.user_id,
                pet_id=pet.id,
                type=canon.type,
                value=canon.value,
                meta=canon.meta,
                created_at=canon.timestamp,
                scored=False
            )
            db.add(event)
            db.flush()  # Get the ID
            created_events.append(event)
            
            # Step 3: Score the event
            canon.pet_id = pet.id  # Assign pet for scoring
            score_deltas = scoring_engine.score_event(canon, pet.id)
            
            # Step 4: Publish score deltas to queue
            for delta in score_deltas:
                queue.publish(SCORE_DELTAS_STREAM, {
                    'delta_type': delta.delta_type,
                    'amount': str(delta.amount),
                    'event_id': str(event.id),
                    'pet_id': str(delta.pet_id),
                    'timestamp': delta.timestamp.isoformat(),
                    'meta': str(delta.meta)
                })
                logger.debug(f"Published {delta.delta_type} delta: {delta.amount}")
            
            # Mark event as scored
            event.scored = True
        
        # EventRaw should already be linked to integration from above
        # No need to do it again here
        
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
