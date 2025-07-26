from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
import logging

from app.db.session import get_db
from app.core.auth import get_current_user
from app.core.analytics_service import AnalyticsService
from app.core.analytics_authorization import AnalyticsAuthorizationService, get_analytics_auth
from app.models.user import User
from app.schemas.analytics import (
    MonthlySummaryResponse, CategoryBreakdownResponse, ReceiptListResponse,
    SpendingTrendsResponse, AnalyticsSummaryResponse, ReceiptSummary,
    AnalyticsQuery, ReceiptListQuery, PaginationParams
)

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/monthly-summary/{year}/{month}", response_model=MonthlySummaryResponse)
async def get_monthly_summary(
    year: int,
    month: int,
    db: Session = Depends(get_db),
    auth_data = Depends(get_analytics_auth)
):
    """
    Get monthly spending summary for a specific year and month.
    
    - **year**: Year (e.g., 2023)
    - **month**: Month (1-12)
    """
    
    auth_service, current_user = auth_data
    
    # Validate month
    if month < 1 or month > 12:
        raise HTTPException(status_code=400, detail="Month must be between 1 and 12")
    
    # Validate year (reasonable range)
    if year < 2000 or year > 2100:
        raise HTTPException(status_code=400, detail="Year must be between 2000 and 2100")
    
    try:
        # Log access for audit
        auth_service.log_analytics_access(current_user, "monthly_summary", {"year": year, "month": month})
        
        analytics_service = AnalyticsService(db)
        summary = analytics_service.get_monthly_summary(current_user.id, year, month)
        
        if not summary:
            raise HTTPException(status_code=404, detail="No data found for the specified month")
        
        return MonthlySummaryResponse(
            success=True,
            message=f"Monthly summary for {year}-{month:02d}",
            data=summary
        )
        
    except Exception as e:
        logger.error(f"Error getting monthly summary: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/category-breakdown", response_model=CategoryBreakdownResponse)
async def get_category_breakdown(
    start_date: Optional[datetime] = Query(None, description="Start date for analysis"),
    end_date: Optional[datetime] = Query(None, description="End date for analysis"),
    category_ids: Optional[List[int]] = Query(None, description="Filter by specific category IDs"),
    min_amount: Optional[float] = Query(None, description="Minimum amount filter"),
    max_amount: Optional[float] = Query(None, description="Maximum amount filter"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get category breakdown of spending for the specified date range.
    
    Returns spending amounts and counts grouped by category.
    """
    
    try:
        query_params = AnalyticsQuery(
            start_date=start_date,
            end_date=end_date,
            category_ids=category_ids,
            min_amount=min_amount,
            max_amount=max_amount
        )
        
        analytics_service = AnalyticsService(db)
        categories = analytics_service.get_category_breakdown(current_user.id, query_params)
        
        date_range_str = ""
        if start_date or end_date:
            start_str = start_date.strftime("%Y-%m-%d") if start_date else "beginning"
            end_str = end_date.strftime("%Y-%m-%d") if end_date else "now"
            date_range_str = f" from {start_str} to {end_str}"
        
        return CategoryBreakdownResponse(
            success=True,
            message=f"Category breakdown{date_range_str}",
            data=categories
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting category breakdown: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/receipts", response_model=ReceiptListResponse)
async def get_receipts(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    search: Optional[str] = Query(None, description="Search in store name or receipt number"),
    category_ids: Optional[List[int]] = Query(None, description="Filter by category IDs"),
    min_amount: Optional[float] = Query(None, description="Minimum amount filter"),
    max_amount: Optional[float] = Query(None, description="Maximum amount filter"),
    sort_by: str = Query("receipt_date", regex="^(receipt_date|total_amount|store_name|created_at)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    db: Session = Depends(get_db),
    auth_data = Depends(get_analytics_auth)
):
    """
    Get paginated list of receipts with filtering and sorting options.
    
    - **page**: Page number (starting from 1)
    - **limit**: Number of items per page (1-100)
    - **search**: Search term for store name or receipt number
    - **sort_by**: Field to sort by (receipt_date, total_amount, store_name, created_at)
    - **sort_order**: Sort direction (asc, desc)
    """
    
    try:
        auth_service, current_user = auth_data
        
        # Validate input parameters
        auth_service.verify_date_range_limits(start_date, end_date)
        auth_service.verify_pagination_limits(page, limit)
        
        # Verify category access if specified
        if category_ids:
            category_ids = auth_service.verify_category_access(current_user, category_ids)
        
        # Log access for audit
        params = {
            "start_date": start_date, "end_date": end_date, "search": search,
            "category_ids": category_ids, "page": page, "limit": limit
        }
        auth_service.log_analytics_access(current_user, "receipt_list", params)
        
        query_params = ReceiptListQuery(
            start_date=start_date,
            end_date=end_date,
            category_ids=category_ids,
            min_amount=min_amount,
            max_amount=max_amount,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        pagination = PaginationParams(page=page, limit=limit)
        
        analytics_service = AnalyticsService(db)
        receipts, total_count = analytics_service.get_receipt_list(
            current_user.id, query_params, pagination
        )
        
        total_pages = (total_count + limit - 1) // limit  # Ceiling division
        
        return ReceiptListResponse(
            success=True,
            message=f"Retrieved {len(receipts)} receipts (page {page} of {total_pages})",
            data=receipts,
            total_count=total_count,
            page=page,
            limit=limit,
            total_pages=total_pages
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting receipt list: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/receipts/{receipt_id}")
async def get_receipt_details(
    receipt_id: int,
    db: Session = Depends(get_db),
    auth_data = Depends(get_analytics_auth)
):
    """
    Get detailed information for a specific receipt including line items.
    """
    
    try:
        auth_service, current_user = auth_data
        
        # Verify receipt ownership and get receipt
        receipt = auth_service.verify_receipt_ownership(current_user, receipt_id)
        
        # Log access for audit
        auth_service.log_analytics_access(current_user, "receipt_details", {"receipt_id": receipt_id})
        
        return {
            "success": True,
            "message": f"Receipt details for {receipt.store_name}",
            "data": receipt
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting receipt details: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/spending-trends", response_model=SpendingTrendsResponse)
async def get_spending_trends(
    start_date: Optional[datetime] = Query(None, description="Start date for trends"),
    end_date: Optional[datetime] = Query(None, description="End date for trends"),
    group_by: str = Query("day", regex="^(day|week|month)$", description="Group spending by time period"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get spending trends over time grouped by specified period.
    
    - **group_by**: Time period to group by (day, week, month)
    - Defaults to last 30 days if no date range provided
    """
    
    try:
        query_params = AnalyticsQuery(
            start_date=start_date,
            end_date=end_date
        )
        
        analytics_service = AnalyticsService(db)
        trends = analytics_service.get_spending_trends(current_user.id, query_params, group_by)
        
        return SpendingTrendsResponse(
            success=True,
            message=f"Spending trends grouped by {group_by}",
            data=trends
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting spending trends: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/summary", response_model=AnalyticsSummaryResponse)
async def get_analytics_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get overall analytics summary for dashboard display.
    
    Includes total receipts, spending amounts, top categories, and recent activity.
    """
    
    try:
        analytics_service = AnalyticsService(db)
        summary = analytics_service.get_analytics_summary(current_user.id)
        
        return AnalyticsSummaryResponse(
            success=True,
            message="Analytics summary retrieved successfully",
            **summary
        )
        
    except Exception as e:
        logger.error(f"Error getting analytics summary: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")