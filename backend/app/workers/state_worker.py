"""
State Update Worker

Consumes score deltas from Redis queue and updates pet state.
Handles idempotency, optimistic locking, and food economy.

Features:
- Idempotent updates (no double-processing)
- Optimistic locking (handles concurrent updates)
- Food cap with overflow → currency conversion
- Graceful error handling
"""
import time
import logging
from uuid import UUID
from datetime import datetime
from typing import Optional

from app.services.queue import QueueService, SCORE_DELTAS_STREAM
from app.core.config import settings
from app.db.database import SessionLocal
from app.db.models import Pet
from app.schemas.scoring import DeltaType
from app.services.cache import CacheService, pet_state_key

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
STREAM_NAME = SCORE_DELTAS_STREAM
GROUP_NAME = 'state-workers'
CONSUMER_NAME = 'state-worker-1'

# Economy settings
FOOD_CAP = 100
OVERFLOW_TO_CURRENCY_RATE = 0.5
MAX_RETRIES = 3

# Initialize cache service for invalidation
cache = CacheService(settings.REDIS_URL)


class StateUpdateWorker:
    """
    Applies score deltas to pet state with idempotency and concurrency safety.
    """
    
    def apply_delta(self, pet_id: UUID, delta_data: dict, db) -> bool:
        """
        Apply a score delta to pet state with idempotency and optimistic locking.
        
        Args:
            pet_id: Pet to update
            delta_data: Score delta from queue containing:
                - event_id: UUID string
                - delta_type: 'food', 'currency', 'happiness', or 'health'
                - amount: Float amount to add
            db: Database session
            
        Returns:
            bool: True if applied, False if already processed
            
        Raises:
            Exception: If update fails after MAX_RETRIES
        """
        event_id = delta_data.get('event_id')
        delta_type = delta_data.get('delta_type')
        amount = float(delta_data.get('amount', 0))
        
        logger.info(f"Applying {delta_type} delta ({amount}) for event {event_id}")
        
        for attempt in range(MAX_RETRIES):
            # Load pet with current version
            pet = db.query(Pet).filter(Pet.id == pet_id).first()
            if not pet:
                logger.error(f"Pet {pet_id} not found")
                return False
            
            # Initialize state if needed
            if not pet.state_json or pet.state_json == {}:
                state = self._get_default_state()
            else:
                # Work with a copy to avoid modifying original during retries
                state = pet.state_json.copy()
            
            # Ensure processed_events list exists
            if "processed_events" not in state:
                state["processed_events"] = []
            
            # Check idempotency - use combination of event_id and delta_type
            # This allows one event to produce multiple deltas (e.g., PR merge → food + happiness)
            delta_key = f"{event_id}:{delta_type}"
            if delta_key in state["processed_events"]:
                logger.info(f"Delta {delta_key} already processed for pet {pet_id}, skipping")
                return False  # Not an error, just already done
            
            # Apply delta based on type
            if delta_type == DeltaType.FOOD:
                self._apply_food_delta(state, amount)
            elif delta_type == DeltaType.CURRENCY:
                state["currency"] = state.get("currency", 0) + amount
            elif delta_type == DeltaType.HAPPINESS:
                new_happiness = state.get("happiness", 50) + amount
                state["happiness"] = max(0, min(100, new_happiness))  # Clamp 0-100
            elif delta_type == DeltaType.HEALTH:
                new_health = state.get("health", 100) + amount
                state["health"] = max(0, min(100, new_health))  # Clamp 0-100
            else:
                logger.warning(f"Unknown delta type: {delta_type}")
                return False
            
            # Track processed delta (event_id + delta_type)
            state["processed_events"].append(delta_key)
            
            # Limit processed events list (keep last 1000 to avoid unbounded growth)
            if len(state["processed_events"]) > 1000:
                state["processed_events"] = state["processed_events"][-1000:]
            
            # Update timestamp
            state["last_updated"] = datetime.utcnow().isoformat()
            
            # Save with optimistic locking
            old_version = pet.version
            new_version = old_version + 1
            
            rows_updated = db.query(Pet).filter(
                Pet.id == pet_id,
                Pet.version == old_version  # Only update if version matches
            ).update({
                "state_json": state,
                "version": new_version,
                "updated_at": datetime.utcnow()
            }, synchronize_session=False)
            
            try:
                db.commit()
            except Exception as e:
                logger.error(f"Commit failed: {e}")
                db.rollback()
                continue
            
            if rows_updated > 0:
                logger.info(
                    f"✅ Applied {delta_type} delta ({amount}) to pet {pet_id}. "
                    f"Version: {old_version} → {new_version}. "
                    f"State: food={state.get('food')}, currency={state.get('currency'):.2f}"
                )
                
                # Invalidate cache since state changed
                cache_key = pet_state_key(str(pet_id))
                cache.delete(cache_key)
                logger.debug(f"Invalidated cache for pet {pet_id}")
                
                return True
            else:
                # Version conflict - someone else updated the pet
                logger.warning(
                    f"Version conflict on pet {pet_id}, retry {attempt + 1}/{MAX_RETRIES}"
                )
                db.rollback()
                time.sleep(0.1 * (attempt + 1))  # Exponential backoff
        
        # Failed after all retries
        raise Exception(f"Failed to update pet {pet_id} after {MAX_RETRIES} retries")
    
    def _apply_food_delta(self, state: dict, amount: float) -> None:
        """
        Apply food delta with cap and overflow handling.
        
        When food exceeds the cap, overflow converts to currency.
        
        Args:
            state: Pet state dict (modified in place)
            amount: Food amount to add
        """
        current_food = state.get("food", 0)
        food_cap = state.get("food_cap", FOOD_CAP)
        
        new_food = current_food + amount
        
        if new_food > food_cap:
            # Handle overflow
            overflow = new_food - food_cap
            overflow_rate = state.get("overflow_to_currency_rate", OVERFLOW_TO_CURRENCY_RATE)
            currency_gained = overflow * overflow_rate
            
            state["food"] = food_cap
            state["currency"] = state.get("currency", 0) + currency_gained
            
            logger.info(
                f"💰 Food overflow: {overflow:.1f} food → {currency_gained:.1f} currency. "
                f"New totals: food={food_cap}, currency={state['currency']:.2f}"
            )
        else:
            # No overflow, just add food
            state["food"] = max(0, new_food)  # Can't go negative
    
    def _get_default_state(self) -> dict:
        """Get default pet state structure."""
        return {
            "food": 0,
            "currency": 0,
            "happiness": 50,
            "health": 100,
            "processed_events": [],
            "food_cap": FOOD_CAP,
            "overflow_to_currency_rate": OVERFLOW_TO_CURRENCY_RATE,
            "last_updated": datetime.utcnow().isoformat()
        }


def process_message(worker: StateUpdateWorker, queue: QueueService, msg_id: str, data: dict):
    """
    Process a single score delta message.
    
    Args:
        worker: StateUpdateWorker instance
        queue: QueueService instance
        msg_id: Redis message ID
        data: Message payload
    """
    db = SessionLocal()
    
    try:
        pet_id_str = data.get('pet_id')
        event_id = data.get('event_id')
        
        if not pet_id_str or not event_id:
            logger.error(f"Message {msg_id} missing pet_id or event_id")
            queue.acknowledge(STREAM_NAME, GROUP_NAME, msg_id)
            return
        
        pet_id = UUID(pet_id_str)
        
        logger.info(f"Processing delta for pet {pet_id}, event {event_id}")
        
        # Apply delta
        applied = worker.apply_delta(pet_id, data, db)
        
        # Always ACK (even if already processed - idempotency handled inside)
        queue.acknowledge(STREAM_NAME, GROUP_NAME, msg_id)
        
        if applied:
            logger.info(f"✅ Successfully processed event {event_id}")
        else:
            logger.info(f"⏭️  Event {event_id} was already processed (idempotent)")
        
    except Exception as e:
        logger.error(f"❌ Error processing message {msg_id}: {e}", exc_info=True)
        db.rollback()
        # Don't ACK on error - message stays in pending for retry
    finally:
        db.close()


def recover_pending_messages(queue: QueueService, worker: StateUpdateWorker):
    """
    Recover any pending messages from previous crashes.
    
    When a worker crashes, messages stay in "pending" state.
    This function reprocesses them on startup.
    """
    logger.info("Checking for pending messages from previous crashes...")
    
    try:
        pending_count = 0
        
        # Read pending messages (messages that were delivered but not ACK'd)
        for msg_id, data in queue.consume(
            STREAM_NAME,
            GROUP_NAME,
            CONSUMER_NAME,
            count=100,
            block=1000
        ):
            logger.info(f"Recovering pending message: {msg_id}")
            process_message(worker, queue, msg_id, data)
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
    2. Create consumer group
    3. Recover pending messages
    4. Process new messages forever
    """
    logger.info(f"Starting state worker: {CONSUMER_NAME}")
    logger.info(f"Redis URL: {settings.REDIS_URL}")
    logger.info(f"Listening to stream: {STREAM_NAME}")
    logger.info(f"Food cap: {FOOD_CAP}, Overflow rate: {OVERFLOW_TO_CURRENCY_RATE}")
    
    queue = QueueService(settings.REDIS_URL)
    worker = StateUpdateWorker()
    
    # Ensure consumer group exists
    try:
        queue.ensure_consumer_group(STREAM_NAME, GROUP_NAME)
        logger.info(f"Consumer group '{GROUP_NAME}' ready")
    except Exception as e:
        logger.error(f"Failed to create consumer group: {e}")
        raise
    
    # Recover any pending messages from crashes
    recover_pending_messages(queue, worker)
    
    logger.info("🚀 State worker started successfully, waiting for deltas...")
    
    # Main processing loop
    while True:
        try:
            # Read new messages from queue
            # count=10: Process up to 10 at once
            # block=5000: Wait up to 5 seconds for new messages
            for msg_id, data in queue.consume(
                STREAM_NAME,
                GROUP_NAME,
                CONSUMER_NAME,
                count=10,
                block=5000
            ):
                process_message(worker, queue, msg_id, data)
                
        except KeyboardInterrupt:
            logger.info("Received shutdown signal, stopping worker...")
            break
            
        except Exception as e:
            logger.error(f"Error in main loop: {e}", exc_info=True)
            time.sleep(5)  # Wait before retrying
    
    logger.info("Worker stopped")


if __name__ == "__main__":
    main()
