from datetime import date
from typing import Optional
from pydantic import BaseModel, Field, validator

from app.schemas.base import ResponseBase


class ExportQuery(BaseModel):
    """Query parameters for export requests."""
    start_date: Optional[date] = Field(None, description="Start date for export range (YYYY-MM-DD)")
    end_date: Optional[date] = Field(None, description="End date for export range (YYYY-MM-DD)")
    include_line_items: bool = Field(True, description="Include line items in separate sheet")
    
    @validator('end_date')
    def end_date_must_be_after_start_date(cls, v, values):
        if v and 'start_date' in values and values['start_date']:
            if v < values['start_date']:
                raise ValueError('end_date must be after or equal to start_date')
        return v


class ExportResponse(BaseModel):
    """Response for export operations."""
    success: bool = Field(True, description="Whether the operation was successful")
    message: str = Field(..., description="Description of the operation result")
    filename: str = Field(..., description="Generated filename for the export")
    records_count: int = Field(..., description="Number of records exported")
    date_range: str = Field(..., description="Date range of exported data")


class ExportStatus(BaseModel):
    """Status information for export operations."""
    status: str = Field(..., description="Status of the export operation")
    filename: Optional[str] = Field(None, description="Filename if export completed")
    error_message: Optional[str] = Field(None, description="Error message if export failed")
    records_processed: int = Field(0, description="Number of records processed")
    created_at: str = Field(..., description="Timestamp when export was initiated")