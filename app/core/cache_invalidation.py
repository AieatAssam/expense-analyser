from typing import Optional
import logging
from sqlalchemy.orm import Session

from app.core.cache_service import analytics_cache
from app.models.receipt import Receipt

logger = logging.getLogger(__name__)

class CacheInvalidationService:
    """Service to handle cache invalidation when data changes"""
    
    @staticmethod
    def invalidate_receipt_analytics(user_id: int, receipt_id: Optional[int] = None):
        """
        Invalidate analytics caches when receipt data changes.
        
        Args:
            user_id: The user whose cache should be invalidated
            receipt_id: Optional specific receipt ID for targeted invalidation
        """
        try:
            analytics_cache.invalidate_on_receipt_change(user_id)
            
            if receipt_id:
                logger.info(f"Cache invalidated for user {user_id} due to receipt {receipt_id} change")
            else:
                logger.info(f"Cache invalidated for user {user_id} due to receipt data change")
                
        except Exception as e:
            logger.error(f"Error invalidating cache for user {user_id}: {e}")
    
    @staticmethod
    def invalidate_user_analytics(user_id: int):
        """Invalidate all analytics cache for a specific user"""
        try:
            analytics_cache.cache.invalidate_user_cache(user_id)
            logger.info(f"All analytics cache invalidated for user {user_id}")
        except Exception as e:
            logger.error(f"Error invalidating all cache for user {user_id}: {e}")

# Create global instance
cache_invalidation = CacheInvalidationService()