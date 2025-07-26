from datetime import date, datetime
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field, validator
from decimal import Decimal


class LineItemEditRequest(BaseModel):
    """Request model for editing a line item."""
    name: str = Field(..., min_length=1, max_length=255, description="Item name")
    description: Optional[str] = Field(None, max_length=500, description="Item description")
    quantity: Optional[float] = Field(1.0, gt=0, description="Item quantity")
    unit_price: Optional[float] = Field(0.0, ge=0, description="Unit price")
    total_price: float = Field(..., ge=0, description="Total price for this line item")
    category_id: Optional[int] = Field(None, description="Category ID")
    category_name: Optional[str] = Field(None, max_length=100, description="Category name (for new categories)")

    @validator('total_price')
    def validate_total_price(cls, v, values):
        if 'quantity' in values and 'unit_price' in values:
            quantity = values.get('quantity', 1.0)
            unit_price = values.get('unit_price', 0.0)
            if quantity and unit_price:
                expected_total = quantity * unit_price
                if abs(v - expected_total) > 0.01:  # Allow small rounding differences
                    # Total price takes precedence, but we'll log this
                    pass
        return v


class LineItemResponse(BaseModel):
    """Response model for line item data."""
    id: int
    name: str
    description: Optional[str]
    quantity: float
    unit_price: float
    total_price: float
    category_id: Optional[int]
    category_name: Optional[str]

    class Config:
        from_attributes = True


class ReceiptEditRequest(BaseModel):
    """Request model for editing receipt data."""
    store_name: Optional[str] = Field(None, min_length=1, max_length=255, description="Store name")
    receipt_date: Optional[date] = Field(None, description="Receipt date")
    total_amount: Optional[float] = Field(None, ge=0, description="Total amount")
    tax_amount: Optional[float] = Field(None, ge=0, description="Tax amount")
    currency: Optional[str] = Field(None, min_length=3, max_length=3, description="Currency code")
    receipt_number: Optional[str] = Field(None, max_length=100, description="Receipt number")
    line_items: Optional[List[LineItemEditRequest]] = Field(None, description="Line items")
    is_verified: Optional[bool] = Field(None, description="Verification status")
    verification_notes: Optional[str] = Field(None, max_length=1000, description="Verification notes")

    @validator('currency')
    def validate_currency(cls, v):
        if v:
            return v.upper()
        return v

    @validator('total_amount')
    def validate_total_amount(cls, v, values):
        if v is not None and 'line_items' in values and values['line_items']:
            line_items_total = sum(item.total_price for item in values['line_items'])
            if abs(v - line_items_total) > 0.05:  # 5 cent tolerance
                # We'll allow this but could add a warning
                pass
        return v


class ReceiptEditResponse(BaseModel):
    """Response model for receipt editing operations."""
    success: bool
    message: str
    receipt_id: Optional[int]
    validation_result: Optional[str]
    confidence_score: Optional[float]
    processed_count: Optional[int] = Field(None, description="Number of receipts processed in bulk operations")


class BulkEditRequest(BaseModel):
    """Request model for bulk editing operations."""
    receipt_ids: List[int] = Field(..., min_items=1, description="List of receipt IDs to edit")
    operation: str = Field(..., description="Bulk operation: 'approve', 'reject', 'assign_category'")
    category_name: Optional[str] = Field(None, description="Category name for assign_category operation")
    notes: Optional[str] = Field(None, max_length=500, description="Notes for the operation")

    @validator('operation')
    def validate_operation(cls, v):
        allowed_operations = ['approve', 'reject', 'assign_category']
        if v not in allowed_operations:
            raise ValueError(f"Operation must be one of: {', '.join(allowed_operations)}")
        return v

    @validator('category_name')
    def validate_category_for_assignment(cls, v, values):
        if values.get('operation') == 'assign_category' and not v:
            raise ValueError("category_name is required for assign_category operation")
        return v


class ReceiptDetailResponse(BaseModel):
    """Detailed response model for receipt data including validation info."""
    id: int
    store_name: str
    receipt_date: Optional[date]
    total_amount: float
    tax_amount: Optional[float]
    currency: str
    receipt_number: Optional[str]
    processing_status: str
    is_verified: bool
    verification_notes: Optional[str]
    image_format: Optional[str]
    line_items: List[LineItemResponse]
    validation_summary: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ValidationSummaryResponse(BaseModel):
    """Response model for validation summary information."""
    validation_result: str
    confidence_score: float
    total_validations: int
    failed_count: int
    warning_count: int
    passed_count: int
    validation_details: Optional[Dict[str, Any]]


class CategoryResponse(BaseModel):
    """Response model for category data."""
    id: int
    name: str
    description: Optional[str]

    class Config:
        from_attributes = True


class ReceiptStatusRequest(BaseModel):
    """Request model for updating receipt status."""
    status: str = Field(..., description="New processing status")
    notes: Optional[str] = Field(None, max_length=1000, description="Status change notes")

    @validator('status')
    def validate_status(cls, v):
        allowed_statuses = [
            'pending', 'processing', 'parsed', 'validated', 
            'completed', 'failed', 'error', 'manual_review'
        ]
        if v not in allowed_statuses:
            raise ValueError(f"Status must be one of: {', '.join(allowed_statuses)}")
        return v


class ReceiptImageResponse(BaseModel):
    """Response model for receipt image data."""
    content_type: str
    filename: str
    size: int