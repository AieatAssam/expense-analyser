import logging
import asyncio
from typing import Dict, Any, Optional, List
from enum import Enum
from datetime import datetime

from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, JSON
from sqlalchemy.orm import Session, relationship

from app.models.base import BaseModel
from app.models.receipt import Receipt
from app.core.websocket_manager import manager

logger = logging.getLogger(__name__)


def serialize_for_json(obj):
    """Helper function to serialize objects for JSON storage"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif hasattr(obj, '__dict__'):
        return str(obj)
    return obj


def make_json_serializable(data: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively make all values in a dictionary JSON serializable"""
    if not isinstance(data, dict):
        return serialize_for_json(data)
    
    result = {}
    for key, value in data.items():
        if isinstance(value, dict):
            result[key] = make_json_serializable(value)
        elif isinstance(value, list):
            result[key] = [serialize_for_json(item) if not isinstance(item, dict) 
                          else make_json_serializable(item) for item in value]
        else:
            result[key] = serialize_for_json(value)
    return result

class ProcessingEventType(str, Enum):
    STARTED = "started"
    PROGRESS = "progress"
    COMPLETED = "completed"
    FAILED = "failed"
    WARNING = "warning"
    ERROR = "error"
    INFO = "info"


class ProcessingEvent(BaseModel):
    """
    Model to track processing events for a receipt, creating a detailed audit trail
    """
    receipt_id = Column(Integer, ForeignKey("receipt.id"), nullable=False, index=True)
    event_type = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False)
    message = Column(String(255), nullable=True)
    timestamp = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    details = Column(JSON, nullable=True)
    
    # Relationships
    receipt = relationship("Receipt", back_populates="processing_events")
    
    def __repr__(self):
        return f"<ProcessingEvent {self.event_type} {self.status} {self.timestamp}>"


class ProcessingStatusTracker:
    """
    Service for tracking and reporting processing status for receipts
    """
    
    def __init__(self, db: Session):
        self.db = db
        
    def create_event(
        self,
        receipt_id: int,
        event_type: ProcessingEventType,
        status: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ) -> ProcessingEvent:
        """Create a new processing event"""
        try:
            # Truncate message if it's too long for the database column
            truncated_message = message[:250] + "..." if len(message) > 250 else message
            
            # Make details JSON serializable
            serializable_details = make_json_serializable(details) if details else {}
            
            event = ProcessingEvent(
                receipt_id=receipt_id,
                event_type=event_type,
                status=status,
                message=truncated_message,
                details=serializable_details
            )
            self.db.add(event)
            self.db.commit()
            self.db.refresh(event)

            # Fire-and-forget websocket notification to the receipt owner
            try:
                self._notify_status_update(event.receipt_id, event.status, truncated_message)
            except Exception:
                # Notification failures must not affect core workflow
                logger.debug("WebSocket notification suppressed due to error", exc_info=True)
            return event
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating processing event: {e}")
            raise
    
    def get_processing_history(self, receipt_id: int) -> List[ProcessingEvent]:
        """Get all processing events for a receipt in chronological order"""
        return self.db.query(ProcessingEvent)\
            .filter(ProcessingEvent.receipt_id == receipt_id)\
            .order_by(ProcessingEvent.timestamp)\
            .all()
    
    def get_latest_event(self, receipt_id: int) -> Optional[ProcessingEvent]:
        """Get the most recent processing event for a receipt"""
        return self.db.query(ProcessingEvent)\
            .filter(ProcessingEvent.receipt_id == receipt_id)\
            .order_by(ProcessingEvent.timestamp.desc())\
            .first()
    
    def get_processing_duration(self, receipt_id: int) -> Optional[float]:
        """Get processing duration in seconds if available"""
        events = self.db.query(ProcessingEvent)\
            .filter(ProcessingEvent.receipt_id == receipt_id)\
            .filter(ProcessingEvent.event_type.in_([ProcessingEventType.STARTED, ProcessingEventType.COMPLETED]))\
            .order_by(ProcessingEvent.timestamp)\
            .all()
        
        if len(events) >= 2:
            start_time = None
            end_time = None
            
            for event in events:
                if event.event_type == ProcessingEventType.STARTED:
                    start_time = event.timestamp
                elif event.event_type == ProcessingEventType.COMPLETED:
                    end_time = event.timestamp
            
            if start_time and end_time:
                return (end_time - start_time).total_seconds()
                
        return None
    
    def has_errors(self, receipt_id: int) -> bool:
        """Check if a receipt has any error events"""
        count = self.db.query(ProcessingEvent)\
            .filter(ProcessingEvent.receipt_id == receipt_id)\
            .filter(ProcessingEvent.event_type == ProcessingEventType.ERROR)\
            .count()
        
        return count > 0
    
    def add_info_event(self, receipt_id: int, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        """Add an informational event"""
        self.create_event(
            receipt_id=receipt_id,
            event_type=ProcessingEventType.INFO,
            status="processing",
            message=message,
            details=details
        )

    def _notify_status_update(self, receipt_id: int, status: str, message: Optional[str]) -> None:
        """Resolve the receipt owner and send a status update over websockets.

        Non-blocking: schedules an asyncio task to deliver the message.
        """
        try:
            # Resolve user_id for targeted broadcast
            receipt = self.db.query(Receipt).filter(Receipt.id == receipt_id).first()
            if not receipt:
                return
            payload = {
                "type": "receipt_status",
                "payload": {
                    "receiptId": str(receipt_id),
                    "status": status,
                    "message": message or "",
                },
            }
            asyncio.create_task(manager.send_json_to_user(receipt.user_id, payload))
        except Exception:
            # Swallow errors to avoid breaking main flow
            logger.debug("Failed to schedule websocket notification", exc_info=True)
    
    def start_processing(self, receipt_id: int, message: str = "Processing started") -> None:
        """Record processing start"""
        self.create_event(
            receipt_id=receipt_id,
            event_type=ProcessingEventType.STARTED,
            status="processing",
            message=message
        )
    
    def record_progress(
        self, 
        receipt_id: int, 
        status: str, 
        message: str, 
        progress_pct: Optional[int] = None
    ) -> None:
        """Record processing progress"""
        details = {"progress_pct": progress_pct} if progress_pct is not None else None
        self.create_event(
            receipt_id=receipt_id,
            event_type=ProcessingEventType.PROGRESS,
            status=status,
            message=message,
            details=details
        )
    
    def complete_processing(self, receipt_id: int, message: str = "Processing completed") -> None:
        """Record processing completion"""
        self.create_event(
            receipt_id=receipt_id,
            event_type=ProcessingEventType.COMPLETED,
            status="completed",
            message=message
        )
    
    def record_error(self, receipt_id: int, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        """Record processing error"""
        self.create_event(
            receipt_id=receipt_id,
            event_type=ProcessingEventType.ERROR,
            status="error",
            message=message,
            details=details
        )
    
    def record_warning(self, receipt_id: int, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        """Record processing warning"""
        self.create_event(
            receipt_id=receipt_id,
            event_type=ProcessingEventType.WARNING,
            status="warning",
            message=message,
            details=details
        )
