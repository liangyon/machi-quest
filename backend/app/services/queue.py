import redis.asyncio as redis
import logging
from typing import Optional, AsyncGenerator, Tuple

logger = logging.getLogger(__name__)

# Queue stream names
WEBHOOK_EVENTS_STREAM = 'webhook-events'


class QueueService:
    """
    Async Redis Stream-based queue service.
    
    Uses async Redis for non-blocking operations and better concurrency.
    """
    
    def __init__(self, redis_url: str, max_connections: int = 20):
        """
        Initialize queue service with connection pooling.
        
        Args:
            redis_url: Redis connection URL
            max_connections: Maximum connections in the pool
        """
        # Create connection pool with proper settings
        # Socket timeout must be longer than the block timeout used in consume (5000ms)
        self.pool = redis.ConnectionPool.from_url(
            redis_url,
            max_connections=max_connections,
            socket_timeout=30,  # 30 second socket timeout (longer than block timeout)
            socket_connect_timeout=5,  # 5 second connect timeout
            decode_responses=True,
            health_check_interval=30  # Check connection health every 30s
        )
        
        # Create async client using the pool
        self.redis_client = redis.Redis(connection_pool=self.pool)
        logger.info("Async Redis queue service initialized")
    
    async def health_check(self) -> bool:
        try:
            await self.redis_client.ping()
            return True
        except redis.RedisError as e:
            logger.error(f"Redis health check failed: {e}")
            return False
    
    async def publish(self, stream: str, data: dict) -> Optional[str]:
        """
        Add message to the Redis stream.
        
        Args:
            stream: Stream name to publish to
            data: Message data as dictionary
            
        Returns:
            Message ID if successful, None on failure
        """
        try:
            message_id = await self.redis_client.xadd(stream, data)
            logger.debug(f"Published message to {stream}: {message_id}")
            return message_id
        except redis.RedisError as e:
            logger.error(f"Error publishing message to {stream}: {e}")
            return None

    async def consume(
        self, 
        stream: str, 
        group: str, 
        consumer: str, 
        count: int = 1, 
        block: int = 5000
    ) -> AsyncGenerator[Tuple[str, dict], None]:
        """
        Read messages from the Redis stream using a consumer group.
        
        Args:
            stream: Stream name to consume from
            group: Consumer group name
            consumer: Consumer name within the group
            count: Number of messages to read at once
            block: Milliseconds to block waiting for messages (0 = forever)
            
        Yields:
            Tuples of (message_id, message_data)
        """
        try:
            messages = await self.redis_client.xreadgroup(
                group, 
                consumer, 
                {stream: '>'}, 
                count=count, 
                block=block
            )
            for stream_name, stream_messages in messages:
                for message_id, message_data in stream_messages:
                    logger.debug(f"Consumed message from {stream}: {message_id}")
                    yield message_id, message_data
        except redis.RedisError as e:
            logger.error(f"Error consuming messages from {stream}: {e}")
            return

    async def acknowledge(self, stream: str, group: str, message_id: str) -> int:
        """
        Acknowledge message processing.
        
        Args:
            stream: Stream name
            group: Consumer group name
            message_id: ID of the message to acknowledge
            
        Returns:
            Number of messages acknowledged (1 if successful, 0 if failed)
        """
        try:
            processed_messages = await self.redis_client.xack(stream, group, message_id)
            if processed_messages:
                logger.debug(f"Acknowledged message {message_id} from {stream}")
            return processed_messages
        except redis.RedisError as e:
            logger.error(f"Error acknowledging message {message_id} from {stream}: {e}")
            return 0
    
    async def ensure_consumer_group(self, stream: str, group: str) -> bool:
        """
        Ensure the consumer group exists.
        Creates the group if it doesn't exist.
        
        Args:
            stream: Stream name
            group: Consumer group name
            
        Returns:
            True if group exists or was created, False on error
        """
        try:
            await self.redis_client.xgroup_create(stream, group, id='0', mkstream=True)
            logger.info(f"Created consumer group '{group}' for stream '{stream}'")
            return True
        except redis.exceptions.ResponseError as e:
            if "BUSYGROUP" in str(e):
                # Group already exists, this is fine
                logger.debug(f"Consumer group '{group}' already exists for stream '{stream}'")
                return True
            else:
                logger.error(f"Error creating consumer group '{group}' for stream '{stream}': {e}")
                return False
        except redis.RedisError as e:
            logger.error(f"Redis error creating consumer group: {e}")
            return False
    
    async def get_stream_info(self, stream: str) -> Optional[dict]:
        """
        Get information about a stream.
        
        Args:
            stream: Stream name
            
        Returns:
            Stream info dict or None on error
        """
        try:
            info = await self.redis_client.xinfo_stream(stream)
            return info
        except redis.ResponseError:
            # Stream doesn't exist
            logger.debug(f"Stream '{stream}' does not exist")
            return None
        except redis.RedisError as e:
            logger.error(f"Error getting stream info for '{stream}': {e}")
            return None
    
    async def close(self) -> None:
        """
        Close Redis connection and cleanup connection pool.
        Call this on application shutdown.
        """
        try:
            if hasattr(self, 'pool'):
                await self.pool.disconnect()
                logger.info("Redis queue connection pool closed")
        except Exception as e:
            logger.error(f"Error closing Redis queue connection: {e}")


# Singleton instance for the queue service
_queue_service_instance = None


def get_redis_client(redis_url: Optional[str] = None) -> QueueService:
    """
    Get or create the singleton QueueService instance.
    
    Args:
        redis_url: Redis connection URL (only used on first call)
        
    Returns:
        QueueService instance
    """
    global _queue_service_instance
    
    if _queue_service_instance is None:
        if redis_url is None:
            # Default to localhost if not provided
            from ..core.config import settings
            redis_url = getattr(settings, 'REDIS_URL', 'redis://localhost:6379')
        
        _queue_service_instance = QueueService(redis_url)
    
    return _queue_service_instance
