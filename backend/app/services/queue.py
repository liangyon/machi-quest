# Purpose: Abstract Redis operations
# What it does: Provides publish() and consume() methods
# Why: Separates queue logic from business logic
import redis

# Queue stream names
WEBHOOK_EVENTS_STREAM = 'webhook-events'
SCORE_DELTAS_STREAM = 'score-deltas'

class QueueService:
    def __init__(self, redis_url):
        """Connect to Redis server."""
        self.redis_client = redis.from_url(redis_url, decode_responses=True)

    def publish(self, stream: str, data: dict) -> str:
        """Add message to the Redis stream."""
        try:
            message_id = self.redis_client.xadd(stream, data)
            return message_id
        except redis.RedisError as e:
            # Handle Redis errors (e.g., connection issues)
            print(f"Error publishing message to {stream}: {e}")
            return None

    def consume(self, stream: str, group: str, consumer: str, count: int = 1, block: int = 5000):
        """Read messages from the Redis stream."""
        try:
            messages = self.redis_client.xreadgroup(group, consumer, {stream: '>'}, count=count, block=block)
            for stream_name, stream_messages in messages:
                for message_id, message_data in stream_messages:
                    yield message_id, message_data
        except redis.RedisError as e:
            print(f"Error consuming messages from {stream}: {e}")
            return 
            

    def acknowledge(self, stream: str, group: str, message_id: str) -> int:
        """Acknowledge message processing."""
        try:
            processed_messages = self.redis_client.xack(stream, group, message_id)
            return processed_messages
        except redis.RedisError as e:
            print(f"Error acknowledging message {message_id} from {stream}: {e}")
            return 0
    
    def ensure_consumer_group(self, stream: str, group: str):
        """Ensure the consumer group exists."""
        try:
            self.redis_client.xgroup_create(stream, group, id='0', mkstream=True)
        except redis.exceptions.ResponseError as e:
            if "BUSYGROUP" in str(e):
                pass  # Group already exists
            else:
                raise
