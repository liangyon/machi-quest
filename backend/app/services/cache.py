"""
Cache Service

Provides Redis caching for frequently accessed data.
"""
import redis
import json
from typing import Optional, Any
import logging

logger = logging.getLogger(__name__)


class CacheService:
    """
    Redis cache service for fast data access.
    
    Features:
    - Get/set with TTL (time to live)
    - Cache invalidation
    - Hit/miss metrics (stored in Redis for multi-worker support)
    - JSON serialization
    - Connection pooling with retry logic
    - Health checks
    
    Improvements:
    - Uses connection pool for better performance
    - Stores metrics in Redis (thread-safe across workers)
    - Configurable timeouts and retries
    """
    
    # Redis keys for metrics
    METRICS_HITS_KEY = "cache:metrics:hits"
    METRICS_MISSES_KEY = "cache:metrics:misses"
    
    def __init__(self, redis_url: str, max_connections: int = 20):
        """
        Initialize cache service with connection pooling.
        
        Args:
            redis_url: Redis connection URL
            max_connections: Maximum connections in the pool
        """
        # Parse redis URL and create connection pool
        try:
            # Create connection pool with proper settings
            self.pool = redis.ConnectionPool.from_url(
                redis_url,
                max_connections=max_connections,
                socket_timeout=5,  # 5 second socket timeout
                socket_connect_timeout=5,  # 5 second connect timeout
                retry_on_timeout=True,
                decode_responses=True,
                health_check_interval=30  # Check connection health every 30s
            )
            
            # Create client using the pool
            self.redis_client = redis.Redis(connection_pool=self.pool)
            
            # Test connection on initialization
            self.redis_client.ping()
            logger.info("Redis cache service initialized successfully")
            
        except redis.RedisError as e:
            logger.error(f"Failed to initialize Redis cache: {e}")
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
    
    def _increment_hits(self) -> None:
        """Increment hit counter in Redis (atomic operation)."""
        try:
            self.redis_client.incr(self.METRICS_HITS_KEY)
        except redis.RedisError as e:
            logger.warning(f"Failed to increment hits metric: {e}")
    
    def _increment_misses(self) -> None:
        """Increment miss counter in Redis (atomic operation)."""
        try:
            self.redis_client.incr(self.METRICS_MISSES_KEY)
        except redis.RedisError as e:
            logger.warning(f"Failed to increment misses metric: {e}")
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        try:
            value = self.redis_client.get(key)
            if value is not None:
                self._increment_hits()
                logger.debug(f"Cache HIT: {key}")
                return json.loads(value)
            else:
                self._increment_misses()
                logger.debug(f"Cache MISS: {key}")
                return None
        except redis.RedisError as e:
            logger.error(f"Cache get error for key {key}: {e}")
            self._increment_misses()
            return None
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error for key {key}: {e}")
            self._increment_misses()
            return None
    
    def set(self, key: str, value: Any, ttl_seconds: int = 300) -> bool:
        """
        Set value in cache with TTL.
        
        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl_seconds: Time to live in seconds (default 5 minutes)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            serialized = json.dumps(value)
            self.redis_client.setex(key, ttl_seconds, serialized)
            logger.debug(f"Cache SET: {key} (TTL: {ttl_seconds}s)")
            return True
        except redis.RedisError as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
        except (TypeError, ValueError) as e:
            logger.error(f"JSON serialize error for key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Delete (invalidate) a cache key.
        
        Args:
            key: Cache key to delete
            
        Returns:
            True if key was deleted, False if didn't exist or error
        """
        try:
            deleted = self.redis_client.delete(key)
            if deleted:
                logger.debug(f"Cache DELETE: {key}")
            return deleted > 0
        except redis.RedisError as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all keys matching a pattern.
        
        Args:
            pattern: Redis pattern (e.g., ":*:state")
            
        Returns:
            Number of keys deleted
        """
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                deleted = self.redis_client.delete(*keys)
                logger.info(f"Cache INVALIDATE: {pattern} ({deleted} keys)")
                return deleted
            return 0
        except redis.RedisError as e:
            logger.error(f"Cache invalidate error for pattern {pattern}: {e}")
            return 0
    
    def get_metrics(self) -> dict:
        """
        Get cache hit/miss metrics from Redis.
        
        Returns:
            Dict with hits, misses, and hit rate
            
        Note: Metrics are now stored in Redis, making them accurate
        across multiple workers/processes.
        """
        try:
            hits = int(self.redis_client.get(self.METRICS_HITS_KEY) or 0)
            misses = int(self.redis_client.get(self.METRICS_MISSES_KEY) or 0)
            total = hits + misses
            hit_rate = (hits / total * 100) if total > 0 else 0
            
            return {
                "hits": hits,
                "misses": misses,
                "total": total,
                "hit_rate_percent": round(hit_rate, 2)
            }
        except redis.RedisError as e:
            logger.error(f"Failed to get metrics: {e}")
            return {
                "hits": 0,
                "misses": 0,
                "total": 0,
                "hit_rate_percent": 0.0,
                "error": "Failed to retrieve metrics"
            }
    
    def reset_metrics(self) -> bool:
        """
        Reset hit/miss counters in Redis.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.redis_client.delete(self.METRICS_HITS_KEY, self.METRICS_MISSES_KEY)
            logger.info("Cache metrics reset")
            return True
        except redis.RedisError as e:
            logger.error(f"Failed to reset metrics: {e}")
            return False
    
    def close(self) -> None:
        """
        Close Redis connection and cleanup connection pool.
        Call this on application shutdown.
        """
        try:
            if hasattr(self, 'pool'):
                self.pool.disconnect()
                logger.info("Redis connection pool closed")
        except Exception as e:
            logger.error(f"Error closing Redis connection: {e}")
