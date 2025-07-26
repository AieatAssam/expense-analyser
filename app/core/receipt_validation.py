import logging
from typing import Dict, Any, Optional, List, Tuple
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, date
from enum import Enum

from sqlalchemy.orm import Session

from app.models.receipt import Receipt
from app.models.line_item import LineItem
from app.core.processing_status import ProcessingStatusTracker, ProcessingEventType, ProcessingEvent

logger = logging.getLogger(__name__)


class ValidationResult(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    REQUIRES_REVIEW = "requires_review"


class ReceiptAccuracyValidator:
    """
    Validates AI parsing accuracy by comparing extracted data with receipt totals
    and implementing confidence scoring for parsed data.
    """
    
    def __init__(self, db: Session, status_tracker: Optional[ProcessingStatusTracker] = None):
        self.db = db
        self.status_tracker = status_tracker or ProcessingStatusTracker(db)
        
        # Validation thresholds (configurable)
        self.total_amount_tolerance = 0.05  # 5% tolerance for total amount discrepancies
        self.min_confidence_score = 0.7     # Minimum confidence score for auto-approval
        self.max_line_item_variance = 0.10  # 10% variance allowed for line item calculations
    
    def validate_receipt_accuracy(
        self, 
        receipt: 'Receipt', 
        parsed_data: Dict[str, Any]
    ) -> Tuple[ValidationResult, float, Dict[str, Any]]:
        """
        Validate the accuracy of parsed receipt data against actual receipt data
        
        Returns:
            ValidationResult: Overall validation result
            float: Confidence score (0.0 - 1.0)
            Dict: Detailed validation results
        """
        try:
            # Log the start of validation
            try:
                self.status_tracker.add_info_event(
                    receipt.id,
                    "Starting accuracy validation for parsed receipt data"
                )
            except Exception as e:
                # Continue validation even if logging fails
                logger.warning(f"Could not log validation start for receipt {receipt.id}: {e}")
            
            validation_results = []
            total_weight = 0
            weighted_score = 0
            
            # 1. Store name validation (weight: 0.2)
            store_weight = 0.2
            store_score = self._calculate_store_name_score(
                receipt.store_name, 
                parsed_data.get("store_name", "")
            )
            validation_results.append({
                "field": "store_name",
                "score": store_score,
                "weight": store_weight,
                "status": "passed" if store_score > 0.7 else "failed",
                "expected": receipt.store_name,
                "actual": parsed_data.get("store_name", "")
            })
            weighted_score += store_score * store_weight
            total_weight += store_weight
            
            # 2. Total amount validation (weight: 0.3)
            total_weight_val = 0.3
            total_score = self._validate_total_amount_score(
                receipt.total_amount,
                parsed_data.get("total_amount", 0)
            )
            validation_results.append({
                "field": "total_amount",
                "score": total_score,
                "weight": total_weight_val,
                "status": "passed" if total_score > 0.7 else "failed",
                "expected": receipt.total_amount,
                "actual": parsed_data.get("total_amount", 0)
            })
            weighted_score += total_score * total_weight_val
            total_weight += total_weight_val
            
            # 3. Date validation (weight: 0.15)
            date_weight = 0.15
            date_score = self._validate_date_score(
                receipt.receipt_date,
                parsed_data.get("date", "")
            )
            validation_results.append({
                "field": "receipt_date",
                "score": date_score,
                "weight": date_weight,
                "status": "passed" if date_score > 0.7 else "failed",
                "expected": receipt.receipt_date,
                "actual": parsed_data.get("date", "")
            })
            weighted_score += date_score * date_weight
            total_weight += date_weight
            
            # 4. Line items validation (weight: 0.35)
            items_weight = 0.35
            items_score = self._validate_line_items_score(
                receipt,
                parsed_data.get("line_items", [])
            )
            validation_results.append({
                "field": "line_items",
                "score": items_score,
                "weight": items_weight,
                "status": "passed" if items_score > 0.7 else "failed",
                "expected": f"{len(receipt.line_items)} items" if hasattr(receipt, 'line_items') else "unknown",
                "actual": f"{len(parsed_data.get('line_items', []))} items"
            })
            weighted_score += items_score * items_weight
            total_weight += items_weight
            
            # Calculate final confidence score
            final_confidence = weighted_score / total_weight if total_weight > 0 else 0.0
            
            # Determine validation result
            if final_confidence >= 0.85:
                result = ValidationResult.PASSED
            elif final_confidence >= 0.6:
                result = ValidationResult.WARNING
            else:
                result = ValidationResult.FAILED
            
            # Create detailed results
            details = {
                "confidence_score": final_confidence,
                "validation_result": result.value,
                "validations": validation_results,
                "confidence_factors": {
                    "overall_score": final_confidence,
                    "total_weight": total_weight,
                    "weighted_score": weighted_score
                }
            }
            
            # Log completion
            try:
                self.status_tracker.add_info_event(
                    receipt.id,
                    f"Accuracy validation completed with {final_confidence:.2f} confidence",
                    details
                )
            except Exception as e:
                logger.warning(f"Could not log validation completion for receipt {receipt.id}: {e}")
            
            return result, final_confidence, details
            
        except Exception as e:
            error_msg = f"Validation error: {str(e)}"
            logger.error(f"Error validating receipt {receipt.id}: {error_msg}")
            
            try:
                self.status_tracker.record_error(
                    receipt.id,
                    error_msg
                )
            except Exception as log_error:
                logger.warning(f"Could not log validation error for receipt {receipt.id}: {log_error}")
            
            return ValidationResult.FAILED, 0.0, {"error": error_msg}
    
    def _validate_total_amount_score(self, expected_total: float, actual_total: float) -> float:
        """Calculate similarity score for total amounts"""
        if expected_total is None or actual_total is None:
            return 0.5
        
        expected = float(expected_total)
        actual = float(actual_total)
        
        if expected == 0 and actual == 0:
            return 1.0
        
        if expected == 0 or actual == 0:
            return 0.0
        
        difference = abs(expected - actual) / max(expected, actual)
        return max(0.0, 1.0 - difference)
    
    def _validate_date_score(self, expected_date, actual_date_str: str) -> float:
        """Calculate similarity score for dates"""
        try:
            if not actual_date_str:
                return 0.0
            
            # Try to parse the date
            from datetime import datetime
            if isinstance(actual_date_str, str):
                # Try common date formats
                for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S"]:
                    try:
                        parsed_date = datetime.strptime(actual_date_str, fmt).date()
                        break
                    except ValueError:
                        continue
                else:
                    return 0.0
            else:
                parsed_date = actual_date_str
            
            if expected_date is None:
                return 0.8  # Give benefit of doubt if no expected date
            
            expected = expected_date.date() if hasattr(expected_date, 'date') else expected_date
            actual = parsed_date
            
            if expected == actual:
                return 1.0
            
            # Allow some tolerance (within 7 days)
            difference = abs((expected - actual).days)
            if difference <= 7:
                return max(0.3, 1.0 - (difference / 7.0))
            
            return 0.0
            
        except Exception:
            return 0.0
    
    def _validate_line_items_score(self, receipt, parsed_items: list) -> float:
        """Calculate similarity score for line items"""
        if not parsed_items:
            return 0.0
        
        if not hasattr(receipt, 'line_items') or not receipt.line_items:
            return 0.8  # Give benefit of doubt if no expected items
        
        expected_items = receipt.line_items
        
        # Compare counts
        count_score = min(len(parsed_items), len(expected_items)) / max(len(parsed_items), len(expected_items))
        
        # Compare total amounts
        parsed_total = sum(float(item.get('amount', 0)) for item in parsed_items)
        expected_total = sum(float(item.total_price or 0) for item in expected_items)
        
        if expected_total == 0 and parsed_total == 0:
            total_score = 1.0
        elif expected_total == 0 or parsed_total == 0:
            total_score = 0.0
        else:
            total_diff = abs(expected_total - parsed_total) / max(expected_total, parsed_total)
            total_score = max(0.0, 1.0 - total_diff)
        
        # Combine scores
        return (count_score * 0.4) + (total_score * 0.6)
    
    def _calculate_store_name_score(self, expected_store: str, actual_store: str) -> float:
        """Calculate similarity score for store names"""
        if not expected_store or not actual_store:
            return 0.0 if not expected_store and not actual_store else 0.5
        
        expected = expected_store.lower().strip()
        actual = actual_store.lower().strip()
        
        if expected == actual:
            return 1.0
        
        # Simple similarity based on common words
        expected_words = set(expected.split())
        actual_words = set(actual.split())
        
        if not expected_words or not actual_words:
            return 0.0
        
        common_words = expected_words.intersection(actual_words)
        similarity = len(common_words) / max(len(expected_words), len(actual_words))
        
        return similarity
    
    def _validate_total_amount(self, receipt: Receipt, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate that extracted total amount matches any existing receipt total"""
        validation = {
            "type": "total_amount",
            "status": "passed",
            "message": "Total amount validation passed",
            "confidence": 1.0,
            "details": {}
        }
        
        try:
            extracted_total = float(extracted_data.get("total_amount", 0))
            receipt_total = float(receipt.total_amount) if receipt.total_amount else 0
            
            validation["details"] = {
                "extracted_total": extracted_total,
                "receipt_total": receipt_total
            }
            
            if receipt_total > 0:  # Only validate if receipt already has a total
                difference = abs(extracted_total - receipt_total)
                tolerance = receipt_total * self.total_amount_tolerance
                
                if difference > tolerance:
                    validation["status"] = "failed"
                    validation["message"] = f"Total amount mismatch: extracted ${extracted_total}, expected ${receipt_total}"
                    validation["confidence"] = 0.3
                    validation["details"]["difference"] = difference
                    validation["details"]["tolerance"] = tolerance
                elif difference > 0:
                    validation["status"] = "warning"
                    validation["message"] = f"Minor total amount difference: ${difference:.2f}"
                    validation["confidence"] = 0.8
                    validation["details"]["difference"] = difference
            else:
                # No existing total to compare against
                if extracted_total <= 0:
                    validation["status"] = "warning"
                    validation["message"] = "Extracted total amount is zero or negative"
                    validation["confidence"] = 0.5
                else:
                    validation["confidence"] = 0.9  # High confidence if reasonable amount
                    
        except (ValueError, TypeError) as e:
            validation["status"] = "failed"
            validation["message"] = f"Invalid total amount format: {str(e)}"
            validation["confidence"] = 0.0
            
        return validation
    
    def _validate_line_items_total(self, receipt: Receipt, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate that line items sum to the receipt total"""
        validation = {
            "type": "line_items_total",
            "status": "passed",
            "message": "Line items total validation passed",
            "confidence": 1.0,
            "details": {}
        }
        
        try:
            line_items = extracted_data.get("line_items", [])
            extracted_total = float(extracted_data.get("total_amount", 0))
            
            if not line_items:
                validation["status"] = "warning"
                validation["message"] = "No line items found in extracted data"
                validation["confidence"] = 0.6
                return validation
            
            # Calculate sum of line items
            line_items_sum = 0.0
            valid_items = 0
            
            for item in line_items:
                try:
                    amount = float(item.get("amount", 0))
                    line_items_sum += amount
                    valid_items += 1
                except (ValueError, TypeError):
                    continue
            
            validation["details"] = {
                "line_items_sum": line_items_sum,
                "extracted_total": extracted_total,
                "line_items_count": len(line_items),
                "valid_items_count": valid_items
            }
            
            if valid_items == 0:
                validation["status"] = "failed"
                validation["message"] = "No valid line item amounts found"
                validation["confidence"] = 0.2
                return validation
            
            # Check if line items sum matches total
            difference = abs(line_items_sum - extracted_total)
            tolerance = max(extracted_total * self.max_line_item_variance, 0.01)
            
            if difference > tolerance:
                validation["status"] = "failed"
                validation["message"] = f"Line items sum (${line_items_sum:.2f}) doesn't match total (${extracted_total:.2f})"
                validation["confidence"] = 0.4
                validation["details"]["difference"] = difference
                validation["details"]["tolerance"] = tolerance
            elif difference > 0.01:  # Minor difference
                validation["status"] = "warning"
                validation["message"] = f"Minor line items sum difference: ${difference:.2f}"
                validation["confidence"] = 0.8
                validation["details"]["difference"] = difference
            else:
                validation["confidence"] = 1.0
                
        except Exception as e:
            validation["status"] = "failed"
            validation["message"] = f"Error validating line items total: {str(e)}"
            validation["confidence"] = 0.0
            
        return validation
    
    def _validate_receipt_date(self, receipt: Receipt, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate receipt date format and reasonableness"""
        validation = {
            "type": "receipt_date",
            "status": "passed",
            "message": "Receipt date validation passed",
            "confidence": 1.0,
            "details": {}
        }
        
        try:
            date_str = extracted_data.get("date")
            
            if not date_str:
                validation["status"] = "warning"
                validation["message"] = "No date found in extracted data"
                validation["confidence"] = 0.5
                return validation
            
            # Try to parse the date
            try:
                parsed_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                validation["details"]["parsed_date"] = date_str
                validation["details"]["date_format"] = "ISO"
            except ValueError:
                # Try alternative formats
                for fmt in ["%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d", "%m-%d-%Y", "%d-%m-%Y"]:
                    try:
                        parsed_date = datetime.strptime(date_str, fmt).date()
                        validation["details"]["parsed_date"] = parsed_date.isoformat()
                        validation["details"]["date_format"] = fmt
                        validation["status"] = "warning"
                        validation["message"] = f"Date parsed with non-standard format: {fmt}"
                        validation["confidence"] = 0.7
                        break
                    except ValueError:
                        continue
                else:
                    validation["status"] = "failed"
                    validation["message"] = f"Unable to parse date: {date_str}"
                    validation["confidence"] = 0.0
                    return validation
            
            # Check if date is reasonable (not too far in future or past)
            today = date.today()
            days_diff = (today - parsed_date).days
            
            if days_diff < -30:  # More than 30 days in future
                validation["status"] = "warning"
                validation["message"] = f"Receipt date is {abs(days_diff)} days in the future"
                validation["confidence"] = 0.6
            elif days_diff > 365 * 5:  # More than 5 years old
                validation["status"] = "warning"
                validation["message"] = f"Receipt date is {days_diff} days old"
                validation["confidence"] = 0.7
            
            validation["details"]["days_from_today"] = days_diff
            
        except Exception as e:
            validation["status"] = "failed"
            validation["message"] = f"Error validating date: {str(e)}"
            validation["confidence"] = 0.0
            
        return validation
    
    def _validate_store_name(self, receipt: Receipt, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate store name quality and completeness"""
        validation = {
            "type": "store_name",
            "status": "passed",
            "message": "Store name validation passed",
            "confidence": 1.0,
            "details": {}
        }
        
        try:
            store_name = extracted_data.get("store_name", "").strip()
            
            validation["details"]["store_name"] = store_name
            validation["details"]["length"] = len(store_name)
            
            if not store_name:
                validation["status"] = "failed"
                validation["message"] = "No store name found"
                validation["confidence"] = 0.2
            elif len(store_name) < 2:
                validation["status"] = "warning"
                validation["message"] = "Store name is very short"
                validation["confidence"] = 0.5
            elif store_name.lower() in ["unknown", "store", "shop", "n/a", "na"]:
                validation["status"] = "warning"
                validation["message"] = "Store name appears to be placeholder text"
                validation["confidence"] = 0.4
            elif not any(c.isalpha() for c in store_name):
                validation["status"] = "warning"
                validation["message"] = "Store name contains no alphabetic characters"
                validation["confidence"] = 0.3
            else:
                # Good store name
                validation["confidence"] = 0.9
                
        except Exception as e:
            validation["status"] = "failed"
            validation["message"] = f"Error validating store name: {str(e)}"
            validation["confidence"] = 0.0
            
        return validation
    
    def _validate_line_items_structure(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate line items structure and completeness"""
        validation = {
            "type": "line_items_structure",
            "status": "passed",
            "message": "Line items structure validation passed",
            "confidence": 1.0,
            "details": {}
        }
        
        try:
            line_items = extracted_data.get("line_items", [])
            
            validation["details"]["total_items"] = len(line_items)
            
            if not line_items:
                validation["status"] = "warning"
                validation["message"] = "No line items found"
                validation["confidence"] = 0.6
                return validation
            
            valid_items = 0
            items_with_names = 0
            items_with_amounts = 0
            items_with_categories = 0
            
            for item in line_items:
                has_required_fields = True
                
                # Check for item name
                name = item.get("name", "").strip()
                if name and len(name) > 1:
                    items_with_names += 1
                else:
                    has_required_fields = False
                
                # Check for item amount
                try:
                    amount = float(item.get("amount", 0))
                    if amount > 0:
                        items_with_amounts += 1
                    else:
                        has_required_fields = False
                except (ValueError, TypeError):
                    has_required_fields = False
                
                # Check for category (optional but good to have)
                category = item.get("category", "").strip()
                if category:
                    items_with_categories += 1
                
                if has_required_fields:
                    valid_items += 1
            
            validation["details"].update({
                "valid_items": valid_items,
                "items_with_names": items_with_names,
                "items_with_amounts": items_with_amounts,
                "items_with_categories": items_with_categories
            })
            
            # Calculate confidence based on completeness
            if valid_items == 0:
                validation["status"] = "failed"
                validation["message"] = "No valid line items found"
                validation["confidence"] = 0.1
            elif valid_items < len(line_items) * 0.5:
                validation["status"] = "warning"
                validation["message"] = f"Only {valid_items}/{len(line_items)} line items are valid"
                validation["confidence"] = 0.4
            elif valid_items < len(line_items):
                validation["status"] = "warning"
                validation["message"] = f"{len(line_items) - valid_items} line items have missing data"
                validation["confidence"] = 0.7
            else:
                validation["confidence"] = 0.9
                
            # Bonus for categorized items
            if items_with_categories > 0:
                category_bonus = min(0.1, items_with_categories / len(line_items) * 0.1)
                validation["confidence"] = min(1.0, validation["confidence"] + category_bonus)
                
        except Exception as e:
            validation["status"] = "failed"
            validation["message"] = f"Error validating line items structure: {str(e)}"
            validation["confidence"] = 0.0
            
        return validation
    
    def _calculate_confidence_score(self, validation_details: Dict[str, Any]) -> float:
        """Calculate overall confidence score based on all validations"""
        try:
            validations = validation_details.get("validations", [])
            
            if not validations:
                return 0.0
            
            # Weight different validation types
            weights = {
                "total_amount": 0.3,
                "line_items_total": 0.3,
                "receipt_date": 0.2,
                "store_name": 0.1,
                "line_items_structure": 0.1
            }
            
            weighted_score = 0.0
            total_weight = 0.0
            
            for validation in validations:
                validation_type = validation.get("type")
                confidence = validation.get("confidence", 0.0)
                weight = weights.get(validation_type, 0.1)
                
                weighted_score += confidence * weight
                total_weight += weight
            
            return weighted_score / total_weight if total_weight > 0 else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating confidence score: {str(e)}")
            return 0.0
    
    def _determine_validation_result(
        self, 
        validation_details: Dict[str, Any], 
        confidence_score: float
    ) -> ValidationResult:
        """Determine overall validation result based on individual validations and confidence"""
        try:
            validations = validation_details.get("validations", [])
            
            # Check for any failed validations
            failed_validations = [v for v in validations if v.get("status") == "failed"]
            if failed_validations:
                return ValidationResult.FAILED
            
            # Check confidence score
            if confidence_score < self.min_confidence_score:
                return ValidationResult.REQUIRES_REVIEW
            
            # Check for warnings
            warning_validations = [v for v in validations if v.get("status") == "warning"]
            if warning_validations:
                return ValidationResult.WARNING
            
            return ValidationResult.PASSED
            
        except Exception as e:
            logger.error(f"Error determining validation result: {str(e)}")
            return ValidationResult.FAILED
    
    def _record_validation_results(
        self, 
        receipt: Receipt, 
        result: ValidationResult, 
        confidence_score: float, 
        validation_details: Dict[str, Any]
    ) -> None:
        """Record validation results in processing events"""
        try:
            message = f"Validation {result.value}: confidence {confidence_score:.2f}"
            
            details = {
                "validation_result": result.value,
                "confidence_score": confidence_score,
                "validation_summary": {
                    "total_validations": len(validation_details.get("validations", [])),
                    "failed_count": len([v for v in validation_details.get("validations", []) if v.get("status") == "failed"]),
                    "warning_count": len([v for v in validation_details.get("validations", []) if v.get("status") == "warning"]),
                    "passed_count": len([v for v in validation_details.get("validations", []) if v.get("status") == "passed"])
                }
            }
            
            if result == ValidationResult.FAILED:
                self.status_tracker.record_error(receipt.id, message, details)
            elif result == ValidationResult.REQUIRES_REVIEW:
                self.status_tracker.record_warning(receipt.id, message, details)
            else:
                self.status_tracker.add_info_event(receipt.id, message, details)
                
        except Exception as e:
            logger.error(f"Error recording validation results: {str(e)}")
    
    def get_validation_summary(self, receipt_id: int) -> Optional[Dict[str, Any]]:
        """Get validation summary for a receipt from processing events"""
        try:
            # Get the latest validation event
            events = self.db.query(ProcessingEvent)\
                .filter(ProcessingEvent.receipt_id == receipt_id)\
                .filter(ProcessingEvent.message.like("Validation %"))\
                .order_by(ProcessingEvent.timestamp.desc())\
                .first()
            
            if events and events.details:
                return events.details
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting validation summary for receipt {receipt_id}: {str(e)}")
            return None