import json
import hashlib
from datetime import datetime, timedelta
from typing import Any, Optional, Dict, List
import logging
from functools import wraps

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from app.core.config import settings

logger = logging.getLogger(__name__)

class CacheService:
    """Redis caching service for analytics data with fallback to in-memory cache"""
    
    def __init__(self):
        self.redis_client = None
        self._memory_cache = {}  # Fallback in-memory cache
        self._memory_cache_ttl = {}  # TTL tracking for memory cache
        
        if REDIS_AVAILABLE:
            try:
                # Try to connect to Redis
                redis_url = getattr(settings, 'REDIS_URL', 'redis://localhost:6379/0')
                self.redis_client = redis.from_url(redis_url, decode_responses=True)
                # Test connection
                self.redis_client.ping()
                logger.info("Connected to Redis cache")
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}. Using in-memory cache.")
                self.redis_client = None
        else:
            logger.warning("Redis not available. Using in-memory cache.")
    
    def _generate_cache_key(self, prefix: str, user_id: int, **kwargs) -> str:
        """Generate a consistent cache key for analytics data"""
        key_parts = [prefix, str(user_id)]
        
        # Sort kwargs for consistent key generation
        for key, value in sorted(kwargs.items()):
            if value is not None:
                if isinstance(value, datetime):
                    value = value.isoformat()
                elif isinstance(value, list):
                    value = ','.join(map(str, sorted(value)))
                key_parts.append(f"{key}:{value}")
        
        key_string = '|'.join(key_parts)
        # Create hash for very long keys
        if len(key_string) > 200:
            hash_object = hashlib.md5(key_string.encode())
            return f"{prefix}:{user_id}:{hash_object.hexdigest()}"
        
        return key_string
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            if self.redis_client:
                value = self.redis_client.get(key)
                if value:
                    return json.loads(value)
            else:
                # Check memory cache with TTL
                if key in self._memory_cache:
                    if key in self._memory_cache_ttl:
                        if datetime.now() > self._memory_cache_ttl[key]:
                            # Expired
                            del self._memory_cache[key]
                            del self._memory_cache_ttl[key]
                            return None
                    return self._memory_cache[key]
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
        
        return None
    
    def set(self, key: str, value: Any, ttl_seconds: int = 300) -> bool:
        """Set value in cache with TTL"""
        try:
            if self.redis_client:
                # Handle Pydantic models and other complex objects
                if hasattr(value, 'model_dump'):
                    # Pydantic v2 model
                    serialized_value = json.dumps(value.model_dump())
                elif hasattr(value, 'dict'):
                    # Pydantic v1 model
                    serialized_value = json.dumps(value.dict())
                elif isinstance(value, list) and value and hasattr(value[0], 'model_dump'):
                    # List of Pydantic v2 models
                    serialized_value = json.dumps([item.model_dump() for item in value])
                elif isinstance(value, list) and value and hasattr(value[0], 'dict'):
                    # List of Pydantic v1 models
                    serialized_value = json.dumps([item.dict() for item in value])
                else:
                    serialized_value = json.dumps(value, default=str)
                return self.redis_client.setex(key, ttl_seconds, serialized_value)
            else:
                # Store in memory cache with TTL
                self._memory_cache[key] = value
                self._memory_cache_ttl[key] = datetime.now() + timedelta(seconds=ttl_seconds)
                
                # Clean up expired entries periodically
                self._cleanup_memory_cache()
                return True
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete value from cache"""
        try:
            if self.redis_client:
                return bool(self.redis_client.delete(key))
            else:
                if key in self._memory_cache:
                    del self._memory_cache[key]
                if key in self._memory_cache_ttl:
                    del self._memory_cache_ttl[key]
                return True
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern"""
        deleted_count = 0
        try:
            if self.redis_client:
                keys = self.redis_client.keys(pattern)
                if keys:
                    deleted_count = self.redis_client.delete(*keys)
            else:
                # Pattern matching for memory cache (simple prefix matching)
                keys_to_delete = []
                for key in self._memory_cache.keys():
                    if pattern.replace('*', '') in key:
                        keys_to_delete.append(key)
                
                for key in keys_to_delete:
                    if key in self._memory_cache:
                        del self._memory_cache[key]
                    if key in self._memory_cache_ttl:
                        del self._memory_cache_ttl[key]
                    deleted_count += 1
                    
        except Exception as e:
            logger.error(f"Cache delete pattern error for pattern {pattern}: {e}")
        
        return deleted_count
    
    def _cleanup_memory_cache(self):
        """Clean up expired entries from memory cache"""
        try:
            now = datetime.now()
            expired_keys = [
                key for key, expiry in self._memory_cache_ttl.items()
                if now > expiry
            ]
            
            for key in expired_keys:
                if key in self._memory_cache:
                    del self._memory_cache[key]
                if key in self._memory_cache_ttl:
                    del self._memory_cache_ttl[key]
                    
        except Exception as e:
            logger.error(f"Memory cache cleanup error: {e}")
    
    def invalidate_user_cache(self, user_id: int):
        """Invalidate all cache entries for a specific user"""
        pattern = f"*:{user_id}:*"
        deleted_count = self.delete_pattern(pattern)
        logger.info(f"Invalidated {deleted_count} cache entries for user {user_id}")
        return deleted_count

# Global cache instance
cache_service = CacheService()

def cache_analytics_data(ttl_seconds: int = 300, key_prefix: str = "analytics"):
    """Decorator for caching analytics function results"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Extract user_id from arguments
            user_id = None
            if args and hasattr(args[0], '__dict__'):
                # First arg might be self (AnalyticsService instance)
                if len(args) > 1:
                    user_id = args[1]  # Second arg should be user_id
            elif 'user_id' in kwargs:
                user_id = kwargs['user_id']
            
            if user_id is None:
                # Can't cache without user_id
                return func(*args, **kwargs)
            
            # Generate cache key
            cache_key = cache_service._generate_cache_key(
                f"{key_prefix}:{func.__name__}",
                user_id,
                **{k: v for k, v in kwargs.items() if k != 'user_id'}
            )
            
            # Try to get from cache
            cached_result = cache_service.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache_service.set(cache_key, result, ttl_seconds)
            logger.debug(f"Cache miss - stored result for {cache_key}")
            
            return result
        
        return wrapper
    return decorator

class AnalyticsCacheManager:
    """Manager for analytics-specific cache operations"""
    
    def __init__(self, cache_service: CacheService):
        self.cache = cache_service
    
    def get_monthly_summary_key(self, user_id: int, year: int, month: int) -> str:
        """Generate cache key for monthly summary"""
        return self.cache._generate_cache_key("monthly_summary", user_id, year=year, month=month)
    
    def get_category_breakdown_key(self, user_id: int, start_date: Optional[datetime], end_date: Optional[datetime]) -> str:
        """Generate cache key for category breakdown"""
        return self.cache._generate_cache_key(
            "category_breakdown", user_id, 
            start_date=start_date, end_date=end_date
        )
    
    def get_receipt_list_key(self, user_id: int, **filters) -> str:
        """Generate cache key for receipt list"""
        return self.cache._generate_cache_key("receipt_list", user_id, **filters)
    
    def invalidate_on_receipt_change(self, user_id: int):
        """Invalidate relevant caches when receipt data changes"""
        patterns_to_clear = [
            f"monthly_summary:{user_id}:*",
            f"category_breakdown:{user_id}:*", 
            f"receipt_list:{user_id}:*",
            f"analytics_summary:{user_id}:*",
            f"spending_trends:{user_id}:*"
        ]
        
        total_deleted = 0
        for pattern in patterns_to_clear:
            deleted = self.cache.delete_pattern(pattern)
            total_deleted += deleted
        
        logger.info(f"Invalidated {total_deleted} analytics cache entries for user {user_id}")
        return total_deleted

# Global analytics cache manager
analytics_cache = AnalyticsCacheManager(cache_service)