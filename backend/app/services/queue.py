"""
Queue Service

Provides Redis Stream operations for message queue functionality.
Used for webhook processing and score delta calculations.
"""
import redis
import logging
from typing import Optional, Generator, Tuple

logger = logging.getLogger(__name__)

# Queue stream names
WEBHOOK_EVENTS_STREAM = 'webhook-events'
SCORE_DELTAS_STREAM = 'score-deltas'


class QueueService:
    """
    Redis Stream-based queue service.
    
    Features:
    - Publish messages to streams
    - Consume messages with consumer groups
    - Message acknowledgment
    - Connection pooling with retry logic
    - Health checks
    
    Improvements:
    - Uses connection pool for better performance
    - Proper logging instead of print statements
    - Configurable timeouts and retries
    - Better error handling
    """
    
    def __init__(self, redis_url: str, max_connections: int = 20):
        """
        Initialize queue service with connection pooling.
        
        Args:
            redis_url: Redis connection URL
            max_connections: Maximum connections in the pool
        """
        try:
            # Create connection pool with proper settings
            # Socket timeout must be longer than the block timeout used in consume (5000ms)
            self.pool = redis.ConnectionPool.from_url(
                redis_url,
                max_connections=max_connections,
                socket_timeout=30,  # 30 second socket timeout (longer than block timeout)
                socket_connect_timeout=5,  # 5 second connect timeout
                retry_on_timeout=True,
                decode_responses=True,
                health_check_interval=30  # Check connection health every 30s
            )
            
            # Create client using the pool
            self.redis_client = redis.Redis(connection_pool=self.pool)
            
            # Test connection on initialization
            self.redis_client.ping()
            logger.info("Redis queue service initialized successfully")
            
        except redis.RedisError as e:
            logger.error(f"Failed to initialize Redis queue: {e}")
            raise
    
    def health_check(self) -> bool:
        """
        Check if Redis connection is healthy.
        
        Returns:
            True if Redis is accessible, False otherwise
        """
        try:
            self.redis_client.ping()
            return True
        except redis.RedisError as e:
            logger.error(f"Redis health check failed: {e}")
            return False
    
    def publish(self, stream: str, data: dict) -> Optional[str]:
        """
        Add message to the Redis stream.
        
        Args:
            stream: Stream name to publish to
            data: Message data as dictionary
            
        Returns:
            Message ID if successful, None on failure
        """
        try:
            message_id = self.redis_client.xadd(stream, data)
            logger.debug(f"Published message to {stream}: {message_id}")
            return message_id
        except redis.RedisError as e:
            logger.error(f"Error publishing message to {stream}: {e}")
            return None

    def consume(
        self, 
        stream: str, 
        group: str, 
        consumer: str, 
        count: int = 1, 
        block: int = 5000
    ) -> Generator[Tuple[str, dict], None, None]:
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
            messages = self.redis_client.xreadgroup(
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

    def acknowledge(self, stream: str, group: str, message_id: str) -> int:
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
            processed_messages = self.redis_client.xack(stream, group, message_id)
            if processed_messages:
                logger.debug(f"Acknowledged message {message_id} from {stream}")
            return processed_messages
        except redis.RedisError as e:
            logger.error(f"Error acknowledging message {message_id} from {stream}: {e}")
            return 0
    
    def ensure_consumer_group(self, stream: str, group: str) -> bool:
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
            self.redis_client.xgroup_create(stream, group, id='0', mkstream=True)
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
    
    def get_stream_info(self, stream: str) -> Optional[dict]:
        """
        Get information about a stream.
        
        Args:
            stream: Stream name
            
        Returns:
            Stream info dict or None on error
        """
        try:
            info = self.redis_client.xinfo_stream(stream)
            return info
        except redis.ResponseError:
            # Stream doesn't exist
            logger.debug(f"Stream '{stream}' does not exist")
            return None
        except redis.RedisError as e:
            logger.error(f"Error getting stream info for '{stream}': {e}")
            return None
    
    def close(self) -> None:
        """
        Close Redis connection and cleanup connection pool.
        Call this on application shutdown.
        """
        try:
            if hasattr(self, 'pool'):
                self.pool.disconnect()
                logger.info("Redis queue connection pool closed")
        except Exception as e:
            logger.error(f"Error closing Redis queue connection: {e}")
