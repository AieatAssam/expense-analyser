from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.receipt_upload import ReceiptUploadService
from app.db.session import get_db
from app.models.user import User
from app.schemas.receipt import FileUploadResponse

router = APIRouter()

@router.post("/upload", response_model=FileUploadResponse)
async def upload_receipt(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload a receipt image for processing.
    
    Supports JPEG, PNG, and PDF formats (max 10MB).
    """
    try:
        # Validate the file
        ReceiptUploadService.validate_file(file)
        
        # Preprocess the image
        processed_image, extension = ReceiptUploadService.preprocess_image(file)
        
        # Store in database
        receipt = ReceiptUploadService.store_receipt_in_db(
            db=db,
            user=current_user,
            file=file,
            processed_image=processed_image,
            extension=extension
        )
        
        # Return receipt ID and status
        return FileUploadResponse(
            status="success",
            receipt_id=receipt.id,
            processing_status=receipt.processing_status
        )
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    
    except Exception as e:
        # Log and convert other exceptions to HTTP exceptions
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error processing receipt upload: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while processing the receipt"
        )
