"""
Tests for the Cache Service.

Tests Redis caching functionality including get/set, TTL, invalidation, and metrics.
"""
import pytest
import time
from uuid import uuid4

from app.services.cache import CacheService, pet_state_key, user_pets_key


class TestCacheService:
    """Test cache service functionality."""
    
    @pytest.fixture
    def cache(self):
        """Create cache service for testing."""
        # Use a test Redis or mock - for now we'll test the interface
        # In real integration tests, you'd use an actual Redis instance
        return CacheService("redis://localhost:6379")
    
    def test_cache_key_builders(self):
        """Test cache key builder functions."""
        pet_id = "12345678-1234-1234-1234-123456789012"
        user_id = "87654321-4321-4321-4321-210987654321"
        
        assert pet_state_key(pet_id) == f"pet:{pet_id}:state"
        assert user_pets_key(user_id) == f"user:{user_id}:pets"
    
    def test_cache_metrics_initialization(self, cache):
        """Test that metrics start at zero."""
        metrics = cache.get_metrics()
        
        assert metrics['hits'] == 0
        assert metrics['misses'] == 0
        assert metrics['total'] == 0
        assert metrics['hit_rate_percent'] == 0
    
    def test_cache_miss_increments_counter(self, cache):
        """Test that cache misses increment the counter."""
        # Reset metrics
        cache.reset_metrics()
        
        # Get non-existent key
        result = cache.get("nonexistent_key")
        
        assert result is None
        metrics = cache.get_metrics()
        assert metrics['misses'] == 1
        assert metrics['hits'] == 0
    
    def test_set_and_get(self, cache):
        """Test setting and getting values."""
        key = f"test_key_{uuid4()}"
        value = {"foo": "bar", "count": 42}
        
        # Set value
        success = cache.set(key, value, ttl_seconds=60)
        assert success is True
        
        # Get value
        result = cache.get(key)
        assert result == value
        
        # Clean up
        cache.delete(key)
    
    def test_cache_hit_increments_counter(self, cache):
        """Test that cache hits increment the counter."""
        cache.reset_metrics()
        
        key = f"test_key_{uuid4()}"
        value = {"test": "data"}
        
        # Set and get
        cache.set(key, value, ttl_seconds=60)
        result = cache.get(key)
        
        assert result == value
        metrics = cache.get_metrics()
        assert metrics['hits'] == 1
        
        # Clean up
        cache.delete(key)
    
    def test_delete_removes_key(self, cache):
        """Test that delete removes a key."""
        key = f"test_key_{uuid4()}"
        value = {"test": "data"}
        
        # Set, delete, try to get
        cache.set(key, value, ttl_seconds=60)
        deleted = cache.delete(key)
        assert deleted is True
        
        result = cache.get(key)
        assert result is None
    
    def test_delete_nonexistent_key(self, cache):
        """Test deleting a key that doesn't exist."""
        deleted = cache.delete(f"nonexistent_{uuid4()}")
        assert deleted is False
    
    def test_hit_rate_calculation(self, cache):
        """Test hit rate percentage calculation."""
        cache.reset_metrics()
        
        key = f"test_key_{uuid4()}"
        cache.set(key, {"data": 1}, ttl_seconds=60)
        
        # 2 hits
        cache.get(key)
        cache.get(key)
        
        # 3 misses
        cache.get("miss1")
        cache.get("miss2")
        cache.get("miss3")
        
        metrics = cache.get_metrics()
        assert metrics['hits'] == 2
        assert metrics['misses'] == 3
        assert metrics['total'] == 5
        assert metrics['hit_rate_percent'] == 40.0  # 2/5 = 40%
        
        # Clean up
        cache.delete(key)
    
    def test_reset_metrics(self, cache):
        """Test resetting metrics."""
        # Generate some hits/misses
        key = f"test_key_{uuid4()}"
        cache.set(key, {"data": 1}, ttl_seconds=60)
        cache.get(key)
        cache.get("miss")
        
        # Reset
        cache.reset_metrics()
        
        metrics = cache.get_metrics()
        assert metrics['hits'] == 0
        assert metrics['misses'] == 0
        
        # Clean up
        cache.delete(key)
