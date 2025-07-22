from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
from app.schemas.base import ResponseBase

class ReceiptBase(BaseModel):
    store_name: Optional[str] = None
    receipt_date: Optional[datetime] = None
    total_amount: Optional[float] = None
    tax_amount: Optional[float] = None
    currency: str = "USD"
    receipt_number: Optional[str] = None

class ReceiptCreate(ReceiptBase):
    # This will be used when creating a receipt from file upload
    pass

class ReceiptUpdate(ReceiptBase):
    # Fields that can be updated
    store_name: Optional[str] = None
    receipt_date: Optional[datetime] = None
    total_amount: Optional[float] = None
    tax_amount: Optional[float] = None
    currency: Optional[str] = None
    receipt_number: Optional[str] = None
    is_verified: Optional[bool] = None
    verification_notes: Optional[str] = None

class ReceiptInDB(ReceiptBase):
    id: int
    user_id: int
    image_path: Optional[str] = None
    processing_status: str
    is_verified: bool
    verification_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class ReceiptResponse(ResponseBase):
    data: ReceiptInDB

class ReceiptListResponse(ResponseBase):
    data: List[ReceiptInDB]

class FileUploadResponse(ResponseBase):
    receipt_id: int
    processing_status: str
    message: str = "Receipt uploaded successfully and queued for processing"
