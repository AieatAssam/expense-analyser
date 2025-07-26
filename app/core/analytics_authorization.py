from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
import logging

from app.core.auth import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.receipt import Receipt
from app.models.account import Account

logger = logging.getLogger(__name__)

class AnalyticsAuthorizationService:
    """Enhanced authorization service for analytics endpoints"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def verify_data_access(self, user: User, target_user_id: int) -> bool:
        """
        Verify that the current user can access data for the target user ID.
        
        Rules:
        - Users can always access their own data
        - Superusers can access any data
        - Account sharing (future feature) would be checked here
        """
        
        # Users can access their own data
        if user.id == target_user_id:
            return True
        
        # Superusers can access any data
        if hasattr(user, 'is_superuser') and user.is_superuser:
            logger.info(f"Superuser {user.email} accessing data for user {target_user_id}")
            return True
        
        # Future: Check for shared account access
        # This would involve checking if the user has been granted access to specific accounts
        
        logger.warning(f"User {user.email} attempted to access data for user {target_user_id}")
        return False
    
    def verify_receipt_ownership(self, user: User, receipt_id: int) -> Receipt:
        """
        Verify that the user owns the specified receipt and return it.
        Raises HTTPException if not authorized.
        """
        
        receipt = self.db.query(Receipt).filter(Receipt.id == receipt_id).first()
        
        if not receipt:
            raise HTTPException(status_code=404, detail="Receipt not found")
        
        if not self.verify_data_access(user, receipt.user_id):
            raise HTTPException(
                status_code=403, 
                detail="You don't have permission to access this receipt"
            )
        
        return receipt
    
    def verify_date_range_limits(self, start_date: Optional[datetime], end_date: Optional[datetime]):
        """
        Verify that date ranges are within reasonable limits to prevent abuse.
        """
        
        if start_date and end_date:
            # Ensure start date is before end date
            if start_date > end_date:
                raise HTTPException(
                    status_code=400, 
                    detail="Start date cannot be after end date"
                )
            
            # Limit maximum date range to prevent excessive queries
            max_range = timedelta(days=3650)  # 10 years
            if (end_date - start_date) > max_range:
                raise HTTPException(
                    status_code=400,
                    detail="Date range cannot exceed 10 years"
                )
        
        # Prevent queries too far in the future
        max_future_date = datetime.now() + timedelta(days=365)
        if end_date and end_date > max_future_date:
            raise HTTPException(
                status_code=400,
                detail="End date cannot be more than 1 year in the future"
            )
    
    def verify_pagination_limits(self, page: int, limit: int):
        """
        Verify pagination parameters are within safe limits.
        """
        
        if page < 1:
            raise HTTPException(status_code=400, detail="Page must be at least 1")
        
        if limit < 1 or limit > 100:
            raise HTTPException(status_code=400, detail="Limit must be between 1 and 100")
        
        # Prevent excessive page numbers (could indicate abuse)
        max_page = 10000
        if page > max_page:
            raise HTTPException(
                status_code=400, 
                detail=f"Page cannot exceed {max_page}"
            )
    
    def verify_category_access(self, user: User, category_ids: List[int]) -> List[int]:
        """
        Verify user has access to the specified categories.
        Returns filtered list of accessible category IDs.
        """
        
        if not category_ids:
            return []
        
        # For now, all categories are accessible to all users
        # In the future, this could be enhanced for multi-tenant category management
        
        return category_ids
    
    def log_analytics_access(self, user: User, endpoint: str, params: dict):
        """
        Log analytics access for audit purposes.
        """
        
        try:
            # Log basic access info (avoid logging sensitive data)
            log_data = {
                "user_id": user.id,
                "user_email": user.email,
                "endpoint": endpoint,
                "timestamp": datetime.now().isoformat(),
                "has_date_range": bool(params.get('start_date') or params.get('end_date')),
                "has_filters": bool(params.get('category_ids') or params.get('search'))
            }
            
            logger.info(f"Analytics access: {log_data}")
            
        except Exception as e:
            logger.error(f"Error logging analytics access: {e}")

# Dependency function for analytics authorization
def get_analytics_auth(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Dependency that provides analytics authorization service and current user.
    """
    auth_service = AnalyticsAuthorizationService(db)
    return auth_service, current_user

def verify_user_data_access(
    target_user_id: int,
    auth_data = Depends(get_analytics_auth)
):
    """
    Dependency that verifies the current user can access data for target_user_id.
    """
    auth_service, current_user = auth_data
    
    if not auth_service.verify_data_access(current_user, target_user_id):
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to access this user's data"
        )
    
    return auth_service, current_user