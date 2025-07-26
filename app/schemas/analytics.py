from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from app.schemas.base import ResponseBase

class CategorySummary(BaseModel):
    category_id: Optional[int]
    category_name: Optional[str] = "Uncategorized"
    total_amount: float
    item_count: int
    
    class Config:
        from_attributes = True

class MonthlySummary(BaseModel):
    year: int
    month: int
    total_amount: float
    receipt_count: int
    categories: List[CategorySummary]
    
    class Config:
        from_attributes = True

class SpendingTrend(BaseModel):
    date: datetime
    amount: float
    receipt_count: int
    
    class Config:
        from_attributes = True

class ReceiptSummary(BaseModel):
    id: int
    store_name: str
    receipt_date: datetime
    total_amount: float
    currency: str
    processing_status: str
    is_verified: bool
    line_item_count: int
    
    class Config:
        from_attributes = True

class AnalyticsQuery(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    category_ids: Optional[List[int]] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None

class PaginationParams(BaseModel):
    page: int = Field(1, ge=1)
    limit: int = Field(20, ge=1, le=100)
    
class ReceiptListQuery(AnalyticsQuery):
    search: Optional[str] = None
    sort_by: Optional[str] = Field("receipt_date", pattern="^(receipt_date|total_amount|store_name|created_at)$")
    sort_order: Optional[str] = Field("desc", pattern="^(asc|desc)$")

class MonthlySummaryResponse(ResponseBase):
    data: MonthlySummary
    
class CategoryBreakdownResponse(ResponseBase):
    data: List[CategorySummary]
    
class ReceiptListResponse(ResponseBase):
    data: List[ReceiptSummary]
    total_count: int
    page: int
    limit: int
    total_pages: int
    
class SpendingTrendsResponse(ResponseBase):
    data: List[SpendingTrend]
    
class AnalyticsSummaryResponse(ResponseBase):
    total_receipts: int
    total_amount: float
    average_receipt_amount: float
    date_range: Dict[str, Optional[datetime]]
    top_categories: List[CategorySummary]
    recent_activity: List[ReceiptSummary]