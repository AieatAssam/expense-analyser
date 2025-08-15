import os
import io
import logging
from datetime import datetime
from typing import Tuple
from fastapi import UploadFile, HTTPException
from PIL import Image, ImageOps, UnidentifiedImageError
from sqlalchemy.orm import Session

from app.models.receipt import Receipt
from app.models.user import User

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "pdf"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

class ReceiptUploadService:
    """Service for handling receipt upload and image processing"""
    
    @staticmethod
    def validate_file(file: UploadFile) -> None:
        """Validate the uploaded file"""
        # Check file extension
        extension = file.filename.split(".")[-1].lower() if file.filename else ""
        if extension not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, 
                              detail=f"File extension not allowed. Supported formats: {', '.join(ALLOWED_EXTENSIONS)}")
        
        # Check file size
        file.file.seek(0, os.SEEK_END)
        file_size = file.file.tell()
        file.file.seek(0)  # Reset file pointer
        
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, 
                              detail=f"File size exceeds maximum limit of {MAX_FILE_SIZE/1024/1024}MB")

    @staticmethod
    def preprocess_image(file: UploadFile) -> Tuple[bytes, str]:
        """Preprocess the image for better quality and return processed image data"""
        try:
            extension = file.filename.split(".")[-1].lower() if file.filename else "jpg"
            
            # Handle PDF files differently
            if extension == "pdf":
                # For PDF files, we don't do image processing, just return the bytes
                content = file.file.read()
                return content, "pdf"
            
            # Process image files
            image = Image.open(io.BytesIO(file.file.read()))

            # Normalize orientation using EXIF if present (common for mobile photos)
            try:
                image = ImageOps.exif_transpose(image)
            except Exception:
                # If no EXIF or unsupported, skip silently
                pass
            
            # Convert to RGB mode if image is in RGBA mode
            if image.mode == 'RGBA':
                image = image.convert('RGB')
                
            # Perform preprocessing steps
            # 1. Resize if too large (preserve aspect ratio)
            max_dimension = 2000  # Max width or height
            if max(image.width, image.height) > max_dimension:
                scale_factor = max_dimension / max(image.width, image.height)
                new_width = int(image.width * scale_factor)
                new_height = int(image.height * scale_factor)
                image = image.resize((new_width, new_height), Image.LANCZOS)
            
            # 2. Auto-enhance image quality
            from PIL import ImageEnhance
            # Enhance contrast
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.2)  # Increase contrast by 20%
            
            # Enhance sharpness
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(1.3)  # Increase sharpness by 30%
            
            # Save optimized image to bytes
            output = io.BytesIO()
            image.save(output, format='JPEG', optimize=True, quality=85)
            return output.getvalue(), "jpg"
            
        except UnidentifiedImageError:
            raise HTTPException(status_code=400, detail="Invalid image file")
        except Exception as e:
            logger.error(f"Error preprocessing image: {str(e)}")
            raise HTTPException(status_code=500, detail="Error processing image")

    @staticmethod
    def store_receipt_in_db(
        db: Session,
        user: User,
        file: UploadFile,
        processed_image: bytes,
        extension: str
    ) -> Receipt:
        """Store receipt data in the database"""
        # Create a binary representation to store in the database
        receipt = Receipt(
            user_id=user.id,
            store_name="Unknown Store",  # Will be updated after LLM processing
            receipt_date=datetime.now(),  # Will be updated after LLM processing
            total_amount=0.0,  # Will be updated after LLM processing
            raw_text=None,  # Will be populated after OCR/LLM processing
            processing_status="uploaded",
            is_verified=False,
            image_data=processed_image,  # Store the image directly in the database
            image_format=extension
        )
        
        db.add(receipt)
        db.commit()
        db.refresh(receipt)
        
        return receipt
