from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.receipt_processor import ReceiptProcessingOrchestrator
from app.core.processing_status import ProcessingStatusTracker
from app.db.session import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.receipt import Receipt
from app.schemas.receipt import (
    ReceiptResponse, 
    ProcessingEventResponse,
    ProcessingStatusResponse
)

router = APIRouter()

@router.post("/{receipt_id}/process", response_model=ReceiptResponse)
async def process_receipt(
    receipt_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Trigger processing of an uploaded receipt.
    Processing happens in the background.
    """
    # Check if receipt exists and belongs to user
    receipt = db.query(Receipt).filter(
        Receipt.id == receipt_id,
        Receipt.user_id == current_user.id
    ).first()
    
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")
    
    # Start processing in background
    background_tasks.add_task(process_receipt_task, receipt_id, db)
    
    return ReceiptResponse.from_orm(receipt)


@router.get("/{receipt_id}/processing/status", response_model=ProcessingStatusResponse)
async def get_receipt_processing_status(
    receipt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get processing status for a receipt
    """
    # Check if receipt exists and belongs to user
    receipt = db.query(Receipt).filter(
        Receipt.id == receipt_id,
        Receipt.user_id == current_user.id
    ).first()
    
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")
    
    # Get status events
    tracker = ProcessingStatusTracker(db)
    events = tracker.get_processing_history(receipt_id)
    latest = tracker.get_latest_event(receipt_id)
    duration = tracker.get_processing_duration(receipt_id)
    has_errors = tracker.has_errors(receipt_id)
    
    # Map to response model
    events_response = [ProcessingEventResponse.from_orm(event) for event in events]
    
    return ProcessingStatusResponse(
        receipt_id=receipt_id,
        current_status=receipt.processing_status,
        events=events_response,
        latest_event=ProcessingEventResponse.from_orm(latest) if latest else None,
        processing_duration_seconds=duration,
        has_errors=has_errors,
        is_completed=receipt.processing_status in ["completed", "manual_review"]
    )


def process_receipt_task(receipt_id: int, db: Session):
    """
    Background task for processing receipt
    """
    # Create a new session for this background task
    # to avoid SQLAlchemy session issues
    from app.db.session import SessionLocal
    
    db_session = SessionLocal()
    try:
        orchestrator = ReceiptProcessingOrchestrator(db_session)
        orchestrator.process_receipt(receipt_id)
    except Exception as e:
        import logging
        logging.error(f"Error in background receipt processing: {str(e)}", exc_info=True)
    finally:
        db_session.close()
