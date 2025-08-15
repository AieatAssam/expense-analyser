from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
import logging
import io
from PIL import Image, ImageOps

from app.db.session import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.receipt import Receipt
from app.models.line_item import LineItem
from app.models.category import Category
from app.schemas.receipt_editing import (
    ReceiptEditRequest, 
    ReceiptEditResponse, 
    BulkEditRequest,
    ReceiptDetailResponse
)
from app.core.receipt_validation import ReceiptAccuracyValidator
from app.core.processing_status import ProcessingStatusTracker

logger = logging.getLogger(__name__)

router = APIRouter()


def make_json_serializable(obj):
    """Convert objects to JSON-serializable format."""
    if hasattr(obj, 'dict'):
        # Pydantic models
        data = obj.dict(exclude_unset=True)
        # Convert dates to strings
        for key, value in data.items():
            if hasattr(value, 'isoformat'):  # date or datetime objects
                data[key] = value.isoformat()
        return data
    elif isinstance(obj, (list, tuple)):
        return [make_json_serializable(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: make_json_serializable(value) for key, value in obj.items()}
    elif hasattr(obj, 'isoformat'):  # date or datetime objects
        return obj.isoformat()
    else:
        return obj


@router.get("/{receipt_id}", response_model=ReceiptDetailResponse)
async def get_receipt_for_editing(
    receipt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get receipt details for editing interface.
    Returns receipt data with line items and validation information.
    """
    try:
        # Get receipt with user authorization check
        receipt = db.query(Receipt).filter(
            Receipt.id == receipt_id,
            Receipt.user_id == current_user.id
        ).first()
        
        if not receipt:
            raise HTTPException(status_code=404, detail="Receipt not found")
        
        # Get line items
        line_items = db.query(LineItem).filter(LineItem.receipt_id == receipt_id).all()
        
        # Get validation information
        validator = ReceiptAccuracyValidator(db)
        validation_summary = validator.get_validation_summary(receipt_id)
        
        # Convert to response format
        response_data = {
            "id": receipt.id,
            "store_name": receipt.store_name,
            "receipt_date": receipt.receipt_date.date() if receipt.receipt_date else None,
            "total_amount": receipt.total_amount,
            "tax_amount": receipt.tax_amount,
            "currency": receipt.currency,
            "receipt_number": receipt.receipt_number,
            "processing_status": receipt.processing_status,
            "is_verified": receipt.is_verified,
            "verification_notes": receipt.verification_notes,
            "image_format": receipt.image_format,
            "line_items": [
                {
                    "id": item.id,
                    "name": item.name,
                    "description": item.description,
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                    "total_price": item.total_price,
                    "category_id": item.category_id,
                    "category_name": item.category.name if item.category else None
                }
                for item in line_items
            ],
            "validation_summary": validation_summary,
            "created_at": receipt.created_at,
            "updated_at": receipt.updated_at
        }
        
        return ReceiptDetailResponse(**response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting receipt {receipt_id} for editing: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving receipt: {str(e)}")


@router.put("/{receipt_id}", response_model=ReceiptEditResponse)
async def update_receipt(
    receipt_id: int,
    edit_request: ReceiptEditRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update receipt information with manual corrections.
    Validates changes and updates validation status.
    """
    try:
        # Get receipt with user authorization check
        receipt = db.query(Receipt).filter(
            Receipt.id == receipt_id,
            Receipt.user_id == current_user.id
        ).first()
        
        if not receipt:
            raise HTTPException(status_code=404, detail="Receipt not found")
        
        # Store original values for audit
        original_data = {
            "store_name": receipt.store_name,
            "receipt_date": receipt.receipt_date.isoformat() if receipt.receipt_date else None,
            "total_amount": float(receipt.total_amount) if receipt.total_amount else None,
            "tax_amount": float(receipt.tax_amount) if receipt.tax_amount else None,
            "currency": receipt.currency,
            "receipt_number": receipt.receipt_number
        }
        
        # Update receipt fields
        if edit_request.store_name is not None:
            receipt.store_name = edit_request.store_name
        
        if edit_request.receipt_date is not None:
            # Convert date to datetime for storage
            receipt.receipt_date = datetime.combine(edit_request.receipt_date, datetime.min.time())
        
        if edit_request.total_amount is not None:
            receipt.total_amount = edit_request.total_amount
        
        if edit_request.tax_amount is not None:
            receipt.tax_amount = edit_request.tax_amount
        
        if edit_request.currency is not None:
            receipt.currency = edit_request.currency
        
        if edit_request.receipt_number is not None:
            receipt.receipt_number = edit_request.receipt_number
        
        # Handle line items updates
        if edit_request.line_items is not None:
            # Remove existing line items
            db.query(LineItem).filter(LineItem.receipt_id == receipt_id).delete()
            
            # Add updated line items
            for item_data in edit_request.line_items:
                # Get or create category if specified
                category_id = None
                if item_data.category_name:
                    category = db.query(Category).filter(Category.name == item_data.category_name).first()
                    if not category:
                        category = Category(
                            name=item_data.category_name,
                            description="Category created during manual editing"
                        )
                        db.add(category)
                        db.flush()  # Get the ID
                    category_id = category.id
                elif item_data.category_id:
                    category_id = item_data.category_id
                
                line_item = LineItem(
                    receipt_id=receipt_id,
                    name=item_data.name,
                    description=item_data.description,
                    quantity=item_data.quantity or 1.0,
                    unit_price=item_data.unit_price or 0.0,
                    total_price=item_data.total_price,
                    category_id=category_id
                )
                db.add(line_item)
        
        # Update verification status
        receipt.is_verified = edit_request.is_verified if edit_request.is_verified is not None else False
        if edit_request.verification_notes:
            receipt.verification_notes = edit_request.verification_notes
        
        # Record audit trail
        status_tracker = ProcessingStatusTracker(db)
        changes = {
            "type": "manual_edit",
            "user_id": current_user.id,
            "original_data": original_data,
            "changes": make_json_serializable(edit_request),
            "edited_at": datetime.utcnow().isoformat()
        }
        
        status_tracker.add_info_event(
            receipt_id,
            f"Receipt manually edited by user {current_user.email}",
            changes
        )
        
        # Re-validate after edits
        validator = ReceiptAccuracyValidator(db, status_tracker)
        extracted_data = {
            "store_name": receipt.store_name,
            "date": receipt.receipt_date.strftime("%Y-%m-%d") if receipt.receipt_date else None,
            "total_amount": receipt.total_amount,
            "line_items": [
                {
                    "name": item.name,
                    "amount": item.total_price,
                    "category": item.category.name if item.category else None
                }
                for item in receipt.line_items
            ]
        }
        
        accuracy_result, confidence_score, accuracy_details = validator.validate_receipt_accuracy(
            receipt, extracted_data
        )
        
        # Commit changes
        db.commit()
        db.refresh(receipt)
        
        logger.info(f"Receipt {receipt_id} updated by user {current_user.id}")
        
        return ReceiptEditResponse(
            success=True,
            message="Receipt updated successfully",
            receipt_id=receipt_id,
            validation_result=accuracy_result.value,
            confidence_score=confidence_score
        )
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating receipt {receipt_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating receipt: {str(e)}")


@router.post("/bulk-edit", response_model=ReceiptEditResponse)
async def bulk_edit_receipts(
    bulk_request: BulkEditRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Perform bulk operations on multiple receipts.
    Supports bulk category assignment, approval, and status changes.
    """
    try:
        # Validate receipt IDs belong to current user
        receipts = db.query(Receipt).filter(
            Receipt.id.in_(bulk_request.receipt_ids),
            Receipt.user_id == current_user.id
        ).all()
        
        if len(receipts) != len(bulk_request.receipt_ids):
            raise HTTPException(
                status_code=404, 
                detail="Some receipts not found or not authorized"
            )
        
        updated_count = 0
        status_tracker = ProcessingStatusTracker(db)
        
        # Perform bulk operations
        if bulk_request.operation == "approve":
            for receipt in receipts:
                receipt.is_verified = True
                receipt.verification_notes = "Bulk approved"
                status_tracker.add_info_event(
                    receipt.id,
                    f"Receipt bulk approved by user {current_user.email}",
                    {"operation": "bulk_approve", "user_id": current_user.id}
                )
                updated_count += 1
                
        elif bulk_request.operation == "reject":
            for receipt in receipts:
                receipt.is_verified = False
                receipt.processing_status = "manual_review"
                receipt.verification_notes = bulk_request.notes or "Bulk rejected"
                status_tracker.add_info_event(
                    receipt.id,
                    f"Receipt bulk rejected by user {current_user.email}",
                    {"operation": "bulk_reject", "user_id": current_user.id}
                )
                updated_count += 1
                
        elif bulk_request.operation == "assign_category" and bulk_request.category_name:
            # Get or create category
            category = db.query(Category).filter(Category.name == bulk_request.category_name).first()
            if not category:
                category = Category(
                    name=bulk_request.category_name,
                    description="Category created during bulk edit"
                )
                db.add(category)
                db.flush()
            
            # Update line items in selected receipts
            for receipt in receipts:
                line_items = db.query(LineItem).filter(LineItem.receipt_id == receipt.id).all()
                for item in line_items:
                    item.category_id = category.id
                
                status_tracker.add_info_event(
                    receipt.id,
                    f"Line items bulk assigned to category '{bulk_request.category_name}' by user {current_user.email}",
                    {"operation": "bulk_assign_category", "category": bulk_request.category_name, "user_id": current_user.id}
                )
                updated_count += 1
        
        # Commit all changes
        db.commit()
        
        logger.info(f"Bulk operation '{bulk_request.operation}' completed on {updated_count} receipts by user {current_user.id}")
        
        return ReceiptEditResponse(
            success=True,
            message=f"Bulk operation completed on {updated_count} receipts",
            receipt_id=None,
            validation_result="bulk_operation",
            confidence_score=1.0,
            processed_count=updated_count
        )
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error performing bulk operation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error performing bulk operation: {str(e)}")


@router.get("/{receipt_id}/image")
async def get_receipt_image(
    receipt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get receipt image for editing interface.
    Returns the raw image data for display alongside editing form.
    """
    try:
        receipt = db.query(Receipt).filter(
            Receipt.id == receipt_id,
            Receipt.user_id == current_user.id
        ).first()
        
        if not receipt:
            raise HTTPException(status_code=404, detail="Receipt not found")
        
        if not receipt.image_data:
            raise HTTPException(status_code=404, detail="Receipt image not found")
        
        # Determine content type based on image format
        content_type = "image/jpeg"  # Default
        format_lower = (receipt.image_format or "jpg").lower()
        if format_lower == "png":
            content_type = "image/png"
        elif format_lower == "pdf":
            content_type = "application/pdf"

        # For PDFs, return raw bytes
        if content_type == "application/pdf":
            from fastapi.responses import Response
            return Response(
                content=receipt.image_data,
                media_type=content_type,
                headers={"Content-Disposition": f"inline; filename=receipt_{receipt_id}.pdf"}
            )

        # For images, normalize orientation using EXIF data to avoid rotated display
        try:
            with Image.open(io.BytesIO(receipt.image_data)) as img:
                img = ImageOps.exif_transpose(img)
                # Ensure RGB for JPEG output
                if content_type == "image/jpeg" and img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
                output = io.BytesIO()
                save_format = "PNG" if content_type == "image/png" else "JPEG"
                save_kwargs = {"optimize": True}
                if save_format == "JPEG":
                    save_kwargs.update({"quality": 85})
                img.save(output, format=save_format, **save_kwargs)
                corrected_bytes = output.getvalue()
        except Exception:
            # Fallback to stored bytes if any processing fails
            corrected_bytes = receipt.image_data

        from fastapi.responses import Response
        ext = "png" if content_type == "image/png" else "jpg"
        return Response(
            content=corrected_bytes,
            media_type=content_type,
            headers={"Content-Disposition": f"inline; filename=receipt_{receipt_id}.{ext}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting receipt image {receipt_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving receipt image: {str(e)}")


@router.get("/", response_model=List[ReceiptDetailResponse])
@router.get("", response_model=List[ReceiptDetailResponse])
async def get_receipts_for_review(
    status: Optional[str] = Query(None, description="Filter by processing status"),
    requires_review: bool = Query(False, description="Filter receipts requiring manual review"),
    skip: int = Query(0, ge=0, description="Number of receipts to skip"),
    limit: int = Query(50, ge=1, le=100, description="Number of receipts to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get list of receipts that require manual review or editing.
    Supports filtering by status and pagination.
    """
    try:
        query = db.query(Receipt).filter(Receipt.user_id == current_user.id)
        
        # Apply filters
        if status:
            query = query.filter(Receipt.processing_status == status)
        
        if requires_review:
            query = query.filter(Receipt.processing_status == "manual_review")
        
        # Order by creation date (newest first)
        query = query.order_by(Receipt.created_at.desc())
        
        # Apply pagination
        receipts = query.offset(skip).limit(limit).all()
        
        # Convert to response format
        response_data = []
        validator = ReceiptAccuracyValidator(db)
        
        for receipt in receipts:
            line_items = db.query(LineItem).filter(LineItem.receipt_id == receipt.id).all()
            validation_summary = validator.get_validation_summary(receipt.id)
            
            receipt_data = {
                "id": receipt.id,
                "store_name": receipt.store_name,
                "receipt_date": receipt.receipt_date.date() if receipt.receipt_date else None,
                "total_amount": receipt.total_amount,
                "tax_amount": receipt.tax_amount,
                "currency": receipt.currency,
                "receipt_number": receipt.receipt_number,
                "processing_status": receipt.processing_status,
                "is_verified": receipt.is_verified,
                "verification_notes": receipt.verification_notes,
                "image_format": receipt.image_format,
                "line_items": [
                    {
                        "id": item.id,
                        "name": item.name,
                        "description": item.description,
                        "quantity": item.quantity,
                        "unit_price": item.unit_price,
                        "total_price": item.total_price,
                        "category_id": item.category_id,
                        "category_name": item.category.name if item.category else None
                    }
                    for item in line_items
                ],
                "validation_summary": validation_summary,
                "created_at": receipt.created_at,
                "updated_at": receipt.updated_at
            }
            
            response_data.append(ReceiptDetailResponse(**receipt_data))
        
        return response_data
        
    except Exception as e:
        logger.error(f"Error getting receipts for review: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving receipts: {str(e)}")