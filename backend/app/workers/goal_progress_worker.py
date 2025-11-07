"""
Goal Progress Worker - Processes webhook events and updates goal progress.

Replaces the old 3-stage pipeline (webhook → scoring → state) with a single worker
that directly updates goals, awards medallions, and tracks growth stages.
"""
import asyncio
import json
import logging
from datetime import date, datetime
from uuid import UUID
from typing import Optional, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..db.database import SessionLocal
from ..models import EventRaw, Goal, User, Integration
from ..repositories.goal_repository import GoalRepository
from ..services.queue import get_redis_client, WEBHOOK_EVENTS_STREAM

logger = logging.getLogger(__name__)

# Configuration constants
MEDALLIONS_PER_GOAL_PER_DAY = 5
CONSUMER_GROUP = "goal-progress-workers"
CONSUMER_NAME = "worker-1"
BLOCK_MS = 5000  # Block for 5 seconds waiting for messages
BATCH_SIZE = 10


class GoalProgressWorker:
    """
    Processes webhook events and updates goal progress.
    
    Responsibilities:
    - Consume events from webhook-events stream
    - Find matching active goals for the user
    - Update goal progress and growth stages
    - Award medallions (max 5 per goal per day)
    - Mark goals as crowned when completed
    """
    
    def __init__(self):
        self.redis = get_redis_client()
        self.running = False
        
    async def start(self):
        """Start the worker loop"""
        self.running = True
        logger.info(f"Starting Goal Progress Worker: {CONSUMER_NAME}")
        
        # Ensure consumer group exists
        try:
            await self.redis.xgroup_create(
                WEBHOOK_EVENTS_STREAM,
                CONSUMER_GROUP,
                id='0',
                mkstream=True
            )
            logger.info(f"Created consumer group: {CONSUMER_GROUP}")
        except Exception as e:
            logger.info(f"Consumer group already exists: {e}")
        
        while self.running:
            try:
                await self.process_batch()
            except Exception as e:
                logger.error(f"Error in worker loop: {e}", exc_info=True)
                await asyncio.sleep(1)
    
    async def stop(self):
        """Stop the worker"""
        self.running = False
        logger.info("Stopping Goal Progress Worker")
    
    async def process_batch(self):
        """Read and process a batch of messages"""
        try:
            # Read messages from stream
            messages = await self.redis.xreadgroup(
                CONSUMER_GROUP,
                CONSUMER_NAME,
                {WEBHOOK_EVENTS_STREAM: '>'},
                count=BATCH_SIZE,
                block=BLOCK_MS
            )
            
            if not messages:
                return
            
            # Process each message
            for stream_name, message_list in messages:
                for message_id, message_data in message_list:
                    try:
                        await self.process_message(message_id, message_data)
                        # ACK the message
                        await self.redis.xack(WEBHOOK_EVENTS_STREAM, CONSUMER_GROUP, message_id)
                    except Exception as e:
                        logger.error(
                            f"Error processing message {message_id}: {e}",
                            exc_info=True
                        )
                        # Don't ACK on error - will retry later
        
        except Exception as e:
            logger.error(f"Error reading from stream: {e}", exc_info=True)
    
    async def process_message(self, message_id: str, message_data: Dict[str, bytes]):
        """Process a single webhook event message"""
        # Decode message data
        data = {k.decode(): v.decode() for k, v in message_data.items()}
        
        event_raw_id = data.get('event_raw_id')
        event_type = data.get('event_type')
        integration_source = data.get('integration_source', 'manual')
        
        logger.info(f"Processing event: {event_type} from {integration_source}")
        
        async with SessionLocal() as db:
            try:
                # Get EventRaw
                event_raw = await db.get(EventRaw, UUID(event_raw_id))
                if not event_raw:
                    logger.warning(f"EventRaw not found: {event_raw_id}")
                    return
                
                # Check if already processed (idempotency)
                if event_raw.processed:
                    logger.info(f"Event already processed: {event_raw_id}")
                    return
                
                # Get user from integration
                user = await self.get_user_from_event(db, event_raw)
                if not user:
                    logger.warning(f"Could not find user for event: {event_raw_id}")
                    event_raw.processed = True
                    await db.commit()
                    return
                
                # Find active goals matching this integration source
                goal_repo = GoalRepository(db)
                active_goals = await goal_repo.get_by_integration(
                    user_id=user.id,
                    integration_source=integration_source
                )
                
                if not active_goals:
                    logger.info(f"No active goals for user {user.id} and source {integration_source}")
                    event_raw.processed = True
                    await db.commit()
                    return
                
                # Process each goal
                for goal in active_goals:
                    await self.update_goal_progress(db, goal, user, event_raw)
                
                # Mark event as processed
                event_raw.processed = True
                await db.commit()
                
                logger.info(
                    f"Successfully processed event for user {user.id}, "
                    f"updated {len(active_goals)} goals"
                )
                
            except Exception as e:
                await db.rollback()
                raise
    
    async def get_user_from_event(
        self,
        db: AsyncSession,
        event_raw: EventRaw
    ) -> Optional[User]:
        """Get user associated with this event"""
        if event_raw.integration_id:
            result = await db.execute(
                select(Integration).where(Integration.id == event_raw.integration_id)
            )
            integration = result.scalar_one_or_none()
            if integration:
                result = await db.execute(
                    select(User).where(User.id == integration.user_id)
                )
                return result.scalar_one_or_none()
        return None
    
    async def update_goal_progress(
        self,
        db: AsyncSession,
        goal: Goal,
        user: User,
        event_raw: EventRaw
    ):
        """Update goal progress and award medallions"""
        goal_repo = GoalRepository(db)
        
        # Increment progress
        amount = 1  # Could be extracted from event payload if needed
        await goal_repo.increment_progress(goal.id, amount)
        
        # Award medallions (max 5 per goal per day)
        today = date.today()
        can_award = (goal.last_completed_date != today) and not goal.is_completed
        
        if can_award:
            updated_goal, medallions_awarded = await goal_repo.award_medallions(
                goal_id=goal.id,
                user_id=user.id,
                amount=MEDALLIONS_PER_GOAL_PER_DAY
            )
            
            if medallions_awarded > 0:
                logger.info(
                    f"Awarded {medallions_awarded} medallions to user {user.id} "
                    f"for goal {goal.id}"
                )
        
        # Log progress update
        logger.info(
            f"Updated goal {goal.id}: progress={goal.current_progress}/{goal.target_value}, "
            f"growth_stage={goal.growth_stage}, crowned={goal.is_crowned}"
        )


async def run_worker():
    """Main entry point for running the worker"""
    worker = GoalProgressWorker()
    try:
        await worker.start()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
        await worker.stop()
    except Exception as e:
        logger.error(f"Worker crashed: {e}", exc_info=True)
        await worker.stop()


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run the worker
    asyncio.run(run_worker())
