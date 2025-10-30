"""
Cache Service

Provides Redis caching for pet state and other frequently accessed data.
"""
import redis
import json
from typing import Optional, Any
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


class CacheService:
    """
    Redis cache service for fast data access.
    
    Features:
    - Get/set with TTL (time to live)
    - Cache invalidation
    - Hit/miss metrics
    - JSON serialization
    """
    
    def __init__(self, redis_url: str):
        """
        Initialize cache service.
        
        Args:
            redis_url: Redis connection URL
        """
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        self.hits = 0
        self.misses = 0
    
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
                self.hits += 1
                logger.debug(f"Cache HIT: {key}")
                return json.loads(value)
            else:
                self.misses += 1
                logger.debug(f"Cache MISS: {key}")
                return None
        except redis.RedisError as e:
            logger.error(f"Cache get error for key {key}: {e}")
            self.misses += 1
            return None
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error for key {key}: {e}")
            self.misses += 1
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
            pattern: Redis pattern (e.g., "pet:*:state")
            
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
        Get cache hit/miss metrics.
        
        Returns:
            Dict with hits, misses, and hit rate
        """
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        
        return {
            "hits": self.hits,
            "misses": self.misses,
            "total": total,
            "hit_rate_percent": round(hit_rate, 2)
        }
    
    def reset_metrics(self):
        """Reset hit/miss counters."""
        self.hits = 0
        self.misses = 0


# Cache key builders
def pet_state_key(pet_id: str) -> str:
    """Build cache key for pet state."""
    return f"pet:{pet_id}:state"


def user_pets_key(user_id: str) -> str:
    """Build cache key for user's pets list."""
    return f"user:{user_id}:pets"
