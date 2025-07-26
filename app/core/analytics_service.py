from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc, asc, text, extract
from sqlalchemy.orm import joinedload
import logging

from app.models.receipt import Receipt
from app.models.line_item import LineItem
from app.models.category import Category
from app.models.user import User
from app.schemas.analytics import (
    MonthlySummary, CategorySummary, SpendingTrend, ReceiptSummary,
    AnalyticsQuery, ReceiptListQuery, PaginationParams
)
from app.core.cache_service import cache_analytics_data, analytics_cache

logger = logging.getLogger(__name__)

class AnalyticsService:
    """Service class for analytics operations with optimized database queries"""
    
    def __init__(self, db: Session):
        self.db = db
    
    @cache_analytics_data(ttl_seconds=3600, key_prefix="monthly_summary")  # 1 hour cache
    def get_monthly_summary(self, user_id: int, year: int, month: int) -> Optional[MonthlySummary]:
        """Get monthly spending summary for a specific user, year, and month"""
        
        # Build date filter for the specific month
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)
        
        # Get total amount and receipt count for the month
        monthly_query = (
            self.db.query(
                func.sum(Receipt.total_amount).label('total_amount'),
                func.count(Receipt.id).label('receipt_count')
            )
            .filter(
                Receipt.user_id == user_id,
                Receipt.receipt_date >= start_date,
                Receipt.receipt_date < end_date
            )
        ).first()
        
        if not monthly_query.total_amount:
            return MonthlySummary(
                year=year,
                month=month,
                total_amount=0.0,
                receipt_count=0,
                categories=[]
            )
        
        # Get category breakdown for the month
        categories = self._get_category_breakdown_for_period(
            user_id, start_date, end_date
        )
        
        return MonthlySummary(
            year=year,
            month=month,
            total_amount=float(monthly_query.total_amount or 0),
            receipt_count=monthly_query.receipt_count,
            categories=categories
        )
    
    @cache_analytics_data(ttl_seconds=1800, key_prefix="category_breakdown")  # 30 minutes cache
    def get_category_breakdown(
        self, 
        user_id: int, 
        query_params: AnalyticsQuery
    ) -> List[CategorySummary]:
        """Get category breakdown for spending analysis"""
        
        start_date, end_date = self._parse_date_range(query_params)
        return self._get_category_breakdown_for_period(user_id, start_date, end_date)
    
    def _get_category_breakdown_for_period(
        self, 
        user_id: int, 
        start_date: Optional[datetime], 
        end_date: Optional[datetime]
    ) -> List[CategorySummary]:
        """Get category breakdown for a specific period"""
        
        # Build subquery for receipt filtering
        receipt_filter = self.db.query(Receipt.id).filter(Receipt.user_id == user_id)
        
        if start_date:
            receipt_filter = receipt_filter.filter(Receipt.receipt_date >= start_date)
        if end_date:
            receipt_filter = receipt_filter.filter(Receipt.receipt_date < end_date)
        
        receipt_ids_subquery = receipt_filter.subquery()
        
        # Query line items with category aggregation
        category_query = (
            self.db.query(
                Category.id.label('category_id'),
                Category.name.label('category_name'),
                func.sum(LineItem.total_price).label('total_amount'),
                func.count(LineItem.id).label('item_count')
            )
            .outerjoin(LineItem, LineItem.category_id == Category.id)
            .filter(LineItem.receipt_id.in_(receipt_ids_subquery))
            .group_by(Category.id, Category.name)
            .order_by(desc('total_amount'))
        ).all()
        
        # Handle uncategorized items
        uncategorized_query = (
            self.db.query(
                func.sum(LineItem.total_price).label('total_amount'),
                func.count(LineItem.id).label('item_count')
            )
            .filter(
                LineItem.receipt_id.in_(receipt_ids_subquery),
                LineItem.category_id.is_(None)
            )
        ).first()
        
        categories = []
        
        # Add categorized items
        for cat in category_query:
            categories.append(CategorySummary(
                category_id=cat.category_id,
                category_name=cat.category_name,
                total_amount=float(cat.total_amount or 0),
                item_count=cat.item_count
            ))
        
        # Add uncategorized items if any
        if uncategorized_query.total_amount:
            categories.append(CategorySummary(
                category_id=None,
                category_name="Uncategorized",
                total_amount=float(uncategorized_query.total_amount),
                item_count=uncategorized_query.item_count
            ))
        
        return categories
    
    def get_receipt_list(
        self, 
        user_id: int, 
        query_params: ReceiptListQuery,
        pagination: PaginationParams
    ) -> Tuple[List[ReceiptSummary], int]:
        """Get paginated receipt list with filtering and sorting"""
        
        # Base query with line item count
        base_query = (
            self.db.query(
                Receipt,
                func.count(LineItem.id).label('line_item_count')
            )
            .outerjoin(LineItem)
            .filter(Receipt.user_id == user_id)
            .group_by(Receipt.id)
        )
        
        # Apply filters
        base_query = self._apply_receipt_filters(base_query, query_params)
        
        # Get total count for pagination
        total_count = base_query.count()
        
        # Apply sorting
        base_query = self._apply_receipt_sorting(base_query, query_params)
        
        # Apply pagination
        offset = (pagination.page - 1) * pagination.limit
        receipts_data = base_query.offset(offset).limit(pagination.limit).all()
        
        # Convert to response objects
        receipts = []
        for receipt_data, line_item_count in receipts_data:
            receipts.append(ReceiptSummary(
                id=receipt_data.id,
                store_name=receipt_data.store_name,
                receipt_date=receipt_data.receipt_date,
                total_amount=receipt_data.total_amount,
                currency=receipt_data.currency,
                processing_status=receipt_data.processing_status,
                is_verified=receipt_data.is_verified,
                line_item_count=line_item_count
            ))
        
        return receipts, total_count
    
    def get_receipt_details(self, user_id: int, receipt_id: int) -> Optional[Receipt]:
        """Get detailed receipt information with line items"""
        
        return (
            self.db.query(Receipt)
            .options(
                joinedload(Receipt.line_items).joinedload(LineItem.category),
                joinedload(Receipt.processing_events)
            )
            .filter(
                Receipt.id == receipt_id,
                Receipt.user_id == user_id
            )
            .first()
        )
    
    @cache_analytics_data(ttl_seconds=1800, key_prefix="spending_trends")  # 30 minutes cache
    def get_spending_trends(
        self, 
        user_id: int, 
        query_params: AnalyticsQuery,
        group_by: str = "day"
    ) -> List[SpendingTrend]:
        """Get spending trends grouped by time period"""
        
        start_date, end_date = self._parse_date_range(query_params)
        
        # Default to last 30 days if no date range provided
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()
        
        # Build grouping based on period
        if group_by == "day":
            date_trunc = func.date_trunc('day', Receipt.receipt_date)
        elif group_by == "week":
            date_trunc = func.date_trunc('week', Receipt.receipt_date)
        elif group_by == "month":
            date_trunc = func.date_trunc('month', Receipt.receipt_date)
        else:
            date_trunc = func.date_trunc('day', Receipt.receipt_date)
        
        trends_query = (
            self.db.query(
                date_trunc.label('date'),
                func.sum(Receipt.total_amount).label('amount'),
                func.count(Receipt.id).label('receipt_count')
            )
            .filter(
                Receipt.user_id == user_id,
                Receipt.receipt_date >= start_date,
                Receipt.receipt_date <= end_date
            )
            .group_by(date_trunc)
            .order_by(date_trunc)
        ).all()
        
        return [
            SpendingTrend(
                date=trend.date,
                amount=float(trend.amount),
                receipt_count=trend.receipt_count
            )
            for trend in trends_query
        ]
    
    @cache_analytics_data(ttl_seconds=600, key_prefix="analytics_summary")  # 10 minutes cache
    def get_analytics_summary(self, user_id: int) -> Dict[str, Any]:
        """Get overall analytics summary for dashboard"""
        
        # Total receipts and amounts
        totals_query = (
            self.db.query(
                func.count(Receipt.id).label('total_receipts'),
                func.sum(Receipt.total_amount).label('total_amount'),
                func.avg(Receipt.total_amount).label('average_amount'),
                func.min(Receipt.receipt_date).label('earliest_date'),
                func.max(Receipt.receipt_date).label('latest_date')
            )
            .filter(Receipt.user_id == user_id)
        ).first()
        
        # Top categories (last 30 days)
        thirty_days_ago = datetime.now() - timedelta(days=30)
        top_categories = self._get_category_breakdown_for_period(
            user_id, thirty_days_ago, None
        )[:5]  # Top 5 categories
        
        # Recent activity (last 10 receipts)
        recent_receipts_data = (
            self.db.query(
                Receipt,
                func.count(LineItem.id).label('line_item_count')
            )
            .outerjoin(LineItem)
            .filter(Receipt.user_id == user_id)
            .group_by(Receipt.id)
            .order_by(desc(Receipt.created_at))
            .limit(10)
            .all()
        )
        
        recent_activity = []
        for receipt_data, line_item_count in recent_receipts_data:
            recent_activity.append(ReceiptSummary(
                id=receipt_data.id,
                store_name=receipt_data.store_name,
                receipt_date=receipt_data.receipt_date,
                total_amount=receipt_data.total_amount,
                currency=receipt_data.currency,
                processing_status=receipt_data.processing_status,
                is_verified=receipt_data.is_verified,
                line_item_count=line_item_count
            ))
        
        return {
            "total_receipts": totals_query.total_receipts or 0,
            "total_amount": float(totals_query.total_amount or 0),
            "average_receipt_amount": float(totals_query.average_amount or 0),
            "date_range": {
                "earliest": totals_query.earliest_date,
                "latest": totals_query.latest_date
            },
            "top_categories": top_categories,
            "recent_activity": recent_activity
        }
    
    def _apply_receipt_filters(self, query, params: ReceiptListQuery):
        """Apply filters to receipt query"""
        
        start_date, end_date = self._parse_date_range(params)
        
        if start_date:
            query = query.filter(Receipt.receipt_date >= start_date)
        if end_date:
            query = query.filter(Receipt.receipt_date <= end_date)
        
        if params.min_amount is not None:
            query = query.filter(Receipt.total_amount >= params.min_amount)
        if params.max_amount is not None:
            query = query.filter(Receipt.total_amount <= params.max_amount)
        
        if params.search:
            search_term = f"%{params.search}%"
            query = query.filter(
                or_(
                    Receipt.store_name.ilike(search_term),
                    Receipt.receipt_number.ilike(search_term)
                )
            )
        
        if params.category_ids:
            # Filter by receipts that have line items in specified categories
            receipt_ids_with_categories = (
                self.db.query(LineItem.receipt_id)
                .filter(LineItem.category_id.in_(params.category_ids))
                .distinct()
                .subquery()
            )
            query = query.filter(Receipt.id.in_(receipt_ids_with_categories))
        
        return query
    
    def _apply_receipt_sorting(self, query, params: ReceiptListQuery):
        """Apply sorting to receipt query"""
        
        sort_column = getattr(Receipt, params.sort_by, Receipt.receipt_date)
        
        if params.sort_order == "asc":
            query = query.order_by(asc(sort_column))
        else:
            query = query.order_by(desc(sort_column))
        
        return query
    
    def _parse_date_range(self, params: AnalyticsQuery) -> Tuple[Optional[datetime], Optional[datetime]]:
        """Parse and validate date range from query parameters"""
        
        start_date = params.start_date if hasattr(params, 'start_date') else None
        end_date = params.end_date if hasattr(params, 'end_date') else None
        
        # Validate date range
        if start_date and end_date and start_date > end_date:
            raise ValueError("Start date cannot be after end date")
        
        return start_date, end_date