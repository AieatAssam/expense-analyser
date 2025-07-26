from datetime import date, datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import logging
from io import BytesIO

from app.db.session import get_db
from app.core.auth import get_current_user
from app.core.export_service import ExportService
from app.models.user import User
from app.schemas.export import ExportQuery, ExportResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/excel", response_class=StreamingResponse)
async def export_receipts_to_excel(
    start_date: Optional[date] = Query(None, description="Start date for export (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date for export (YYYY-MM-DD)"),
    include_line_items: bool = Query(True, description="Include line items in separate sheet"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Export receipts and expense data to Excel format.
    
    - **start_date**: Optional start date for filtering (YYYY-MM-DD)
    - **end_date**: Optional end date for filtering (YYYY-MM-DD)  
    - **include_line_items**: Whether to include line items in a separate sheet (default: true)
    
    Returns an Excel file containing:
    - Summary sheet with export statistics
    - Receipts summary sheet with all receipt data
    - Line items detail sheet (if include_line_items=true)
    """
    
    try:
        # Validate date range
        if start_date and end_date and end_date < start_date:
            raise HTTPException(
                status_code=400, 
                detail="end_date must be after or equal to start_date"
            )
        
        # Log export request for audit
        logger.info(
            f"Excel export requested by user {current_user.id} "
            f"(start_date: {start_date}, end_date: {end_date}, "
            f"include_line_items: {include_line_items})"
        )
        
        # Create export service and generate Excel
        export_service = ExportService(db)
        excel_buffer, filename = export_service.export_receipts_to_excel(
            user_id=current_user.id,
            start_date=start_date,
            end_date=end_date,
            include_line_items=include_line_items
        )
        
        # Set appropriate headers for file download
        headers = {
            'Content-Disposition': f'attachment; filename="{filename}"',
            'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        }
        
        # Create streaming response with proper file handling
        def generate_excel():
            try:
                # Read the buffer content
                content = excel_buffer.getvalue()
                # Yield content in chunks for better memory management
                chunk_size = 8192  # 8KB chunks
                for i in range(0, len(content), chunk_size):
                    yield content[i:i + chunk_size]
            except Exception as e:
                logger.error(f"Error streaming Excel file for user {current_user.id}: {str(e)}")
                raise
            finally:
                # Ensure buffer is closed
                excel_buffer.close()
        
        logger.info(f"Excel export completed successfully for user {current_user.id}: {filename}")
        
        return StreamingResponse(
            generate_excel(),
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers=headers
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during Excel export for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to generate Excel export: {str(e)}"
        )


@router.post("/excel/info", response_model=ExportResponse)
async def get_export_info(
    query: ExportQuery,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get information about what would be exported without actually generating the file.
    
    This endpoint allows users to preview export parameters and record counts
    before initiating the actual export process.
    """
    
    try:
        # Create export service to get data info
        export_service = ExportService(db)
        
        # Get receipts data for counting (without generating Excel)
        receipts_data = export_service._get_receipts_data(
            user_id=current_user.id,
            start_date=query.start_date,
            end_date=query.end_date
        )
        
        # Generate date range string
        if query.start_date or query.end_date:
            start_str = query.start_date.strftime("%Y-%m-%d") if query.start_date else "Beginning"
            end_str = query.end_date.strftime("%Y-%m-%d") if query.end_date else "Present"
            date_range = f"{start_str} to {end_str}"
        else:
            date_range = "All time"
        
        # Generate filename preview
        filename = export_service._generate_filename(query.start_date, query.end_date)
        
        return ExportResponse(
            success=True,
            message=f"Export preview for {len(receipts_data)} receipts",
            filename=filename,
            records_count=len(receipts_data),
            date_range=date_range
        )
        
    except Exception as e:
        logger.error(f"Error getting export info for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get export information: {str(e)}"
        )