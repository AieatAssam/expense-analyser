import logging
from enum import Enum
from typing import Dict, Any, Optional, List
import base64
import time
import io
from PIL import Image, ImageOps

from sqlalchemy.orm import Session

from app.models.receipt import Receipt
from app.models.line_item import LineItem
from app.models.category import Category
from app.core.llm_client import LLMClient
from app.core.receipt_prompts import get_prompt
from app.core.llm_response_validation import LLMReceiptValidator
from app.core.processing_status import ProcessingStatusTracker, ProcessingEventType
from app.core.receipt_validation import ReceiptAccuracyValidator, ValidationResult

logger = logging.getLogger(__name__)

class ProcessingStatus(str, Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    PARSED = "parsed"
    VALIDATED = "validated"
    COMPLETED = "completed"
    FAILED = "failed"
    ERROR = "error"
    MANUAL_REVIEW = "manual_review"


class ReceiptProcessingOrchestrator:
    """
    Orchestrates the entire receipt processing workflow:
    1. Initialize processing for an uploaded receipt
    2. Extract text and data using LLM
    3. Validate extracted data
    4. Store structured data in database
    5. Track processing status throughout
    """
    
    def __init__(
        self, 
        db: Session,
        llm_client: Optional[LLMClient] = None,
        validator: Optional[LLMReceiptValidator] = None,
        status_tracker: Optional[ProcessingStatusTracker] = None,
        accuracy_validator: Optional[ReceiptAccuracyValidator] = None,
        receipt_type: str = "default",
    ):
        self.db = db
        self.llm_client = llm_client or LLMClient()
        self.validator = validator or LLMReceiptValidator()
        self.status_tracker = status_tracker or ProcessingStatusTracker(db)
        self.accuracy_validator = accuracy_validator or ReceiptAccuracyValidator(db, status_tracker)
        self.receipt_type = receipt_type
    
    def process_receipt(self, receipt_id: int) -> Receipt:
        """
        Process a receipt through the entire workflow.
        Returns the updated receipt model.
        """
        start_ts = time.time()
        try:
            # Get the receipt from the database
            receipt = self._get_receipt(receipt_id)
            if not receipt:
                logger.error(
                    "receipt not found",
                    extra={"receipt_id": receipt_id},
                )
                return None
            
            # Update status to processing and record start event
            self._update_receipt_status(receipt, ProcessingStatus.PROCESSING)
            self.status_tracker.start_processing(receipt_id)
            logger.info(
                "processing started",
                extra={
                    "receipt_id": receipt_id,
                    "image_format": getattr(receipt, "image_format", None),
                    "has_image": bool(getattr(receipt, "image_data", None)),
                    "llm_provider": self.llm_client.provider_name,
                },
            )
            
            # Extract data from receipt image
            self.status_tracker.record_progress(receipt_id, "extracting", "Extracting data from receipt image", 25)
            step_ts = time.time()
            extracted_data = self._extract_receipt_data(receipt)
            logger.info(
                "extraction finished",
                extra={
                    "receipt_id": receipt_id,
                    "duration_ms": int((time.time() - step_ts) * 1000),
                    "ok": bool(extracted_data),
                },
            )
            
            if not extracted_data:
                self._update_receipt_status(receipt, ProcessingStatus.FAILED, "Failed to extract data from receipt")
                self.status_tracker.record_error(receipt_id, "Failed to extract data from receipt image")
                return receipt
            
            self.status_tracker.record_progress(receipt_id, "extracted", "Successfully extracted data from receipt", 50)
                
            # Validate extracted data structure
            self.status_tracker.record_progress(receipt_id, "validating", "Validating extracted data structure", 60)
            step_ts = time.time()
            is_valid, validation_errors = self.validator.validate(extracted_data)
            logger.info(
                "structure validation finished",
                extra={
                    "receipt_id": receipt_id,
                    "duration_ms": int((time.time() - step_ts) * 1000),
                    "is_valid": is_valid,
                    "errors_count": len(validation_errors or []),
                },
            )
            
            if not is_valid:
                self._update_receipt_status(
                    receipt, 
                    ProcessingStatus.MANUAL_REVIEW, 
                    f"Structure validation errors: {', '.join(validation_errors)}"
                )
                self.status_tracker.record_warning(
                    receipt_id, 
                    f"Structure validation errors: {', '.join(validation_errors)}",
                    {"errors": validation_errors}
                )
                logger.warning(f"Receipt {receipt_id} structure validation failed: {validation_errors}")
            else:
                self._update_receipt_status(receipt, ProcessingStatus.VALIDATED)
                self.status_tracker.record_progress(receipt_id, "validated", "Data structure validation successful", 65)
            
            # Perform accuracy validation
            self.status_tracker.record_progress(receipt_id, "accuracy_check", "Performing accuracy validation", 70)
            step_ts = time.time()
            accuracy_result, confidence_score, accuracy_details = self.accuracy_validator.validate_receipt_accuracy(
                receipt, extracted_data
            )
            logger.info(
                "accuracy validation finished",
                extra={
                    "receipt_id": receipt_id,
                    "duration_ms": int((time.time() - step_ts) * 1000),
                    "result": str(accuracy_result),
                    "confidence": float(confidence_score),
                },
            )
            
            # Update receipt status based on accuracy validation
            if accuracy_result == ValidationResult.FAILED:
                self._update_receipt_status(
                    receipt,
                    ProcessingStatus.MANUAL_REVIEW,
                    f"Accuracy validation failed: confidence {confidence_score:.2f}"
                )
                logger.warning(f"Receipt {receipt_id} accuracy validation failed with confidence {confidence_score:.2f}")
            elif accuracy_result == ValidationResult.REQUIRES_REVIEW:
                self._update_receipt_status(
                    receipt,
                    ProcessingStatus.MANUAL_REVIEW,
                    f"Low confidence score: {confidence_score:.2f}, requires manual review"
                )
                logger.info(f"Receipt {receipt_id} requires manual review due to low confidence: {confidence_score:.2f}")
            elif accuracy_result == ValidationResult.WARNING:
                # Keep as validated but note warnings
                self.status_tracker.record_warning(
                    receipt_id,
                    f"Accuracy validation passed with warnings: confidence {confidence_score:.2f}",
                    accuracy_details
                )
                logger.info(f"Receipt {receipt_id} accuracy validation passed with warnings: {confidence_score:.2f}")
            else:
                # Passed accuracy validation
                self.status_tracker.record_progress(receipt_id, "accuracy_validated", "Accuracy validation passed", 75)
                logger.info(f"Receipt {receipt_id} accuracy validation passed with confidence {confidence_score:.2f}")
            
            # Map and store structured data
            self.status_tracker.record_progress(receipt_id, "storing", "Storing receipt data in database", 85)
            step_ts = time.time()
            self._store_receipt_data(receipt, extracted_data)
            logger.info(
                "store finished",
                extra={
                    "receipt_id": receipt_id,
                    "duration_ms": int((time.time() - step_ts) * 1000),
                },
            )
            
            # Update final status
            if receipt.processing_status != ProcessingStatus.MANUAL_REVIEW:
                self._update_receipt_status(receipt, ProcessingStatus.COMPLETED)
                self.status_tracker.complete_processing(receipt_id, "Receipt processing completed successfully")
            else:
                self.status_tracker.record_progress(
                    receipt_id, 
                    "manual_review", 
                    "Receipt requires manual review due to validation errors", 
                    100
                )
            
            logger.info(
                "processing finished",
                extra={
                    "receipt_id": receipt_id,
                    "final_status": str(receipt.processing_status),
                    "total_duration_ms": int((time.time() - start_ts) * 1000),
                },
            )
            return receipt
            
        except Exception as e:
            logger.error(
                "processing error",
                extra={"receipt_id": receipt_id, "error": str(e)},
                exc_info=True,
            )
            try:
                receipt = self._get_receipt(receipt_id)
                if receipt:
                    self._update_receipt_status(receipt, ProcessingStatus.ERROR, f"Error: {str(e)}")
                    self.status_tracker.record_error(receipt_id, f"Processing error: {str(e)}")
            except Exception as inner_e:
                logger.error(
                    "failed to update receipt status after error",
                    extra={"receipt_id": receipt_id, "error": str(inner_e)},
                )

            raise
    
    def _get_receipt(self, receipt_id: int) -> Receipt:
        """Get receipt from database with ID"""
        return self.db.query(Receipt).filter(Receipt.id == receipt_id).first()
    
    def _update_receipt_status(self, receipt: Receipt, status: ProcessingStatus, notes: str = None) -> None:
        """Update receipt processing status and commit to db"""
        receipt.processing_status = status
        if notes:
            receipt.verification_notes = notes
        self.db.add(receipt)
        self.db.commit()
        self.db.refresh(receipt)
        logger.info(f"Receipt {receipt.id} status updated to {status}")
    
    def _extract_receipt_data(self, receipt: Receipt) -> Dict[str, Any]:
        """
        Extract structured data from receipt image using LLM.
        Returns dict with extracted data or None if extraction failed.
        """
        try:
            # Check if we have image data to process
            if not receipt.image_data:
                self.status_tracker.record_error(receipt.id, "Receipt has no image data")
                raise ValueError("Receipt has no image data")
            
            # Encode image as base64 for LLM processing
            # Normalize orientation using EXIF (skip PDFs)
            corrected_bytes = receipt.image_data
            try:
                fmt_lower = (receipt.image_format or "jpg").lower()
                if fmt_lower != "pdf" and receipt.image_data:
                    with Image.open(io.BytesIO(receipt.image_data)) as img:
                        img = ImageOps.exif_transpose(img)
                        # Ensure RGB for JPEG output
                        if fmt_lower in ("jpg", "jpeg") and img.mode in ("RGBA", "P"):
                            img = img.convert("RGB")
                        out = io.BytesIO()
                        save_format = "PNG" if fmt_lower == "png" else "JPEG"
                        save_kwargs = {"optimize": True}
                        if save_format == "JPEG":
                            save_kwargs.update({"quality": 85})
                        img.save(out, format=save_format, **save_kwargs)
                        corrected_bytes = out.getvalue()
            except Exception:
                # On any error, fall back to original bytes
                corrected_bytes = receipt.image_data

            image_base64 = base64.b64encode(corrected_bytes).decode('utf-8')
            
            # Get prompt template for receipt type
            prompt = get_prompt(self.receipt_type)
            self.status_tracker.add_info_event(
                receipt.id, 
                f"Using receipt prompt template: {self.receipt_type}"
            )
            
            # Call LLM with prompt and image
            params = {
                "image_data": image_base64,
                "image_format": receipt.image_format,
                "temperature": 0.2,  # Lower temperature for more deterministic output
                "max_tokens": 65536
            }
            
            self.status_tracker.add_info_event(
                receipt.id, 
                f"Sending request to LLM provider: {self.llm_client.provider_name}"
            )
            
            # Retry logic built into LLMClient will handle retries and provider failover
            req_ts = time.time()
            llm_response = self.llm_client.send(prompt, params=params)
            logger.info(
                "llm call finished",
                extra={
                    "receipt_id": receipt.id,
                    "provider": self.llm_client.provider_name,
                    "duration_ms": int((time.time() - req_ts) * 1000),
                },
            )
            
            if not llm_response or "response" not in llm_response:
                error_msg = f"Invalid LLM response format for receipt {receipt.id}"
                logger.error(error_msg)
                self.status_tracker.record_error(receipt.id, error_msg)
                return None
            
            self.status_tracker.add_info_event(
                receipt.id, 
                "Received response from LLM provider"
            )
                
            # Parse JSON from response
            try:
                extracted_data = llm_response["response"]
                if isinstance(extracted_data, str):
                    import json
                    extracted_data = json.loads(extracted_data)
                    
                # Store raw extracted text for debugging/reference
                receipt.raw_text = str(llm_response)
                self.db.add(receipt)
                self.db.commit()
                
                self.status_tracker.add_info_event(
                    receipt.id, 
                    "Successfully parsed LLM response"
                )
                
                return extracted_data
            except Exception as json_error:
                logger.error(
                    "failed to parse llm response",
                    extra={"receipt_id": receipt.id, "error": str(json_error)},
                )
                self.status_tracker.record_warning(
                    receipt.id, 
                    f"Failed to parse LLM response: {str(json_error)}",
                    {"raw_response": str(llm_response)}
                )
                
                receipt.raw_text = str(llm_response)
                self.db.add(receipt)
                self.db.commit()
                
                # Try fallback parsing
                if "response" in llm_response and isinstance(llm_response["response"], str):
                    logger.info("attempting fallback parsing", extra={"receipt_id": receipt.id})
                    self.status_tracker.add_info_event(
                        receipt.id, 
                        "Attempting fallback parsing with regex"
                    )
                    fallback_data = self.validator.fallback_parse(llm_response["response"])
                    if fallback_data:
                        self.status_tracker.add_info_event(
                            receipt.id, 
                            "Fallback parsing successful"
                        )
                    return fallback_data
                return None
                
        except Exception as e:
            logger.error(
                "error extracting data from receipt",
                extra={"receipt_id": receipt.id, "error": str(e)},
                exc_info=True,
            )
            self.status_tracker.record_error(
                receipt.id, 
                f"Error extracting data: {str(e)}"
            )
            return None
    
    def _store_receipt_data(self, receipt: Receipt, data: Dict[str, Any]) -> None:
        """
        Store structured receipt data in the database.
        Updates receipt model and creates line items.
        """
        from datetime import datetime
        
        try:
            # Update receipt with extracted data
            self.status_tracker.add_info_event(
                receipt.id, 
                "Updating receipt data from extracted information"
            )
            
            receipt.store_name = data.get("store_name", "Unknown Store")
            
            # Parse and set date
            try:
                date_str = data.get("date")
                if date_str:
                    receipt.receipt_date = datetime.strptime(date_str, "%Y-%m-%d")
            except Exception as date_error:
                logger.warning(f"Failed to parse date for receipt {receipt.id}: {str(date_error)}")
                self.status_tracker.record_warning(
                    receipt.id, 
                    f"Failed to parse date: {str(date_error)}",
                    {"date_string": data.get("date")}
                )
            
            receipt.total_amount = data.get("total_amount", 0.0)
            receipt.is_verified = False  # Requires manual verification
            
            # Save updated receipt
            self.db.add(receipt)
            self.db.commit()
            self.status_tracker.add_info_event(
                receipt.id, 
                f"Updated receipt: {receipt.store_name}, {receipt.receipt_date}, ${receipt.total_amount}"
            )
            
            # Process line items
            self.status_tracker.add_info_event(
                receipt.id, 
                f"Processing {len(data.get('line_items', []))} line items"
            )
            self._process_line_items(receipt, data.get("line_items", []))
            
        except Exception as e:
            logger.error(f"Error storing receipt data for receipt {receipt.id}: {str(e)}", exc_info=True)
            self.status_tracker.record_error(
                receipt.id, 
                f"Error storing receipt data: {str(e)}"
            )
            self.db.rollback()
            raise
    
    def _process_line_items(self, receipt: Receipt, line_items: List[Dict[str, Any]]) -> None:
        """Process and store line items with categories"""
        try:
            # Delete any existing line items for this receipt
            existing_count = self.db.query(LineItem).filter(LineItem.receipt_id == receipt.id).count()
            if existing_count > 0:
                self.status_tracker.add_info_event(
                    receipt.id, 
                    f"Removing {existing_count} existing line items"
                )
                self.db.query(LineItem).filter(LineItem.receipt_id == receipt.id).delete()
            
            # Create new line items
            created_count = 0
            for item_data in line_items:
                # Find or create category
                category = None
                category_name = item_data.get("category")
                if category_name:
                    category = self._get_or_create_category(category_name)
                
                # Create line item
                line_item = LineItem(
                    name=item_data.get("name", "Unknown Item"),
                    quantity=1.0,  # Default quantity
                    unit_price=item_data.get("amount", 0.0),
                    total_price=item_data.get("amount", 0.0),
                    receipt_id=receipt.id,
                    category_id=category.id if category else None
                )
                
                self.db.add(line_item)
                created_count += 1
            
            self.db.commit()
            self.status_tracker.add_info_event(
                receipt.id, 
                f"Created {created_count} new line items with categories"
            )
        except Exception as e:
            logger.error(f"Error processing line items for receipt {receipt.id}: {str(e)}", exc_info=True)
            self.status_tracker.record_error(
                receipt.id, 
                f"Error processing line items: {str(e)}"
            )
            self.db.rollback()
            raise
    
    def _get_or_create_category(self, category_name: str) -> Category:
        """Get existing category or create a new one"""
        category = self.db.query(Category).filter(Category.name == category_name).first()
        if not category:
            category = Category(
                name=category_name,
                description=f"Auto-generated category for {category_name}"
            )
            self.db.add(category)
            self.db.commit()
            self.db.refresh(category)
        
        return category
