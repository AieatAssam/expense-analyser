import logging
from enum import Enum
from typing import Dict, Any, Optional, List
import base64

from sqlalchemy.orm import Session

from app.models.receipt import Receipt
from app.models.line_item import LineItem
from app.models.category import Category
from app.core.llm_client import LLMClient
from app.core.receipt_prompts import get_prompt
from app.core.llm_response_validation import LLMReceiptValidator
from app.core.processing_status import ProcessingStatusTracker, ProcessingEventType

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
        receipt_type: str = "default",
    ):
        self.db = db
        self.llm_client = llm_client or LLMClient()
        self.validator = validator or LLMReceiptValidator()
        self.status_tracker = status_tracker or ProcessingStatusTracker(db)
        self.receipt_type = receipt_type
    
    def process_receipt(self, receipt_id: int) -> Receipt:
        """
        Process a receipt through the entire workflow.
        Returns the updated receipt model.
        """
        try:
            # Get the receipt from the database
            receipt = self._get_receipt(receipt_id)
            if not receipt:
                logger.error(f"Receipt {receipt_id} not found")
                return None
            
            # Update status to processing and record start event
            self._update_receipt_status(receipt, ProcessingStatus.PROCESSING)
            self.status_tracker.start_processing(receipt_id)
            
            # Extract data from receipt image
            self.status_tracker.record_progress(receipt_id, "extracting", "Extracting data from receipt image", 25)
            extracted_data = self._extract_receipt_data(receipt)
            
            if not extracted_data:
                self._update_receipt_status(receipt, ProcessingStatus.FAILED, "Failed to extract data from receipt")
                self.status_tracker.record_error(receipt_id, "Failed to extract data from receipt image")
                return receipt
            
            self.status_tracker.record_progress(receipt_id, "extracted", "Successfully extracted data from receipt", 50)
                
            # Validate extracted data
            self.status_tracker.record_progress(receipt_id, "validating", "Validating extracted data", 60)
            is_valid, validation_errors = self.validator.validate(extracted_data)
            
            if not is_valid:
                self._update_receipt_status(
                    receipt, 
                    ProcessingStatus.MANUAL_REVIEW, 
                    f"Validation errors: {', '.join(validation_errors)}"
                )
                self.status_tracker.record_warning(
                    receipt_id, 
                    f"Validation errors: {', '.join(validation_errors)}",
                    {"errors": validation_errors}
                )
                logger.warning(f"Receipt {receipt_id} validation failed: {validation_errors}")
            else:
                self._update_receipt_status(receipt, ProcessingStatus.VALIDATED)
                self.status_tracker.record_progress(receipt_id, "validated", "Data validation successful", 75)
            
            # Map and store structured data
            self.status_tracker.record_progress(receipt_id, "storing", "Storing receipt data in database", 85)
            self._store_receipt_data(receipt, extracted_data)
            
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
            
            return receipt
            
        except Exception as e:
            logger.error(f"Error processing receipt {receipt_id}: {str(e)}", exc_info=True)
            try:
                receipt = self._get_receipt(receipt_id)
                if receipt:
                    self._update_receipt_status(receipt, ProcessingStatus.ERROR, f"Error: {str(e)}")
                    self.status_tracker.record_error(receipt_id, f"Processing error: {str(e)}")
            except Exception as inner_e:
                logger.error(f"Failed to update receipt status: {str(inner_e)}")
            
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
            image_base64 = base64.b64encode(receipt.image_data).decode('utf-8')
            
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
                "max_tokens": 1024
            }
            
            self.status_tracker.add_info_event(
                receipt.id, 
                f"Sending request to LLM provider: {self.llm_client.provider_name}"
            )
            
            # Retry logic built into LLMClient will handle retries and provider failover
            llm_response = self.llm_client.send(prompt, params=params)
            
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
                logger.error(f"Failed to parse LLM response: {str(json_error)}")
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
                    logger.info(f"Attempting fallback parsing for receipt {receipt.id}")
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
            logger.error(f"Error extracting data from receipt {receipt.id}: {str(e)}", exc_info=True)
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
