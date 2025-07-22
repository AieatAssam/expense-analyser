#!/usr/bin/env python
"""
Test script for receipt upload endpoint.
This script creates a simple test image and sends it to the API.
"""

import sys
import requests
from PIL import Image, ImageDraw
import io

# Configuration
API_URL = "http://localhost:8000/api/v1/receipts/upload"
AUTH_TOKEN = ""  # Add your Auth0 token here

def create_test_receipt_image(text="Test Receipt", size=(800, 1200), format="JPEG"):
    """Create a test receipt image with text"""
    # Create a white background
    image = Image.new('RGB', size, color=(255, 255, 255))
    draw = ImageDraw.Draw(image)
    
    # Add some text and elements to make it look like a receipt
    draw.rectangle([(50, 50), (size[0] - 50, size[1] - 50)], outline=(0, 0, 0))
    
    # Add header
    draw.text((size[0] // 2 - 100, 100), text, fill=(0, 0, 0))
    
    # Add store name
    draw.text((100, 200), "Store: Test Grocery Store", fill=(0, 0, 0))
    
    # Add date
    draw.text((100, 250), "Date: 2025-07-19", fill=(0, 0, 0))
    
    # Add items
    y_pos = 350
    for i in range(1, 6):
        draw.text((100, y_pos), f"Item {i}", fill=(0, 0, 0))
        draw.text((400, y_pos), f"${i * 2.50:.2f}", fill=(0, 0, 0))
        y_pos += 50
    
    # Add total
    draw.line([(100, y_pos), (500, y_pos)], fill=(0, 0, 0))
    y_pos += 50
    draw.text((100, y_pos), "Total:", fill=(0, 0, 0))
    draw.text((400, y_pos), "$37.50", fill=(0, 0, 0))
    
    # Save to bytes
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format=format)
    img_byte_arr.seek(0)
    
    return img_byte_arr

def upload_receipt(image_bytes, filename="test_receipt.jpg"):
    """Upload the receipt image to the API"""
    if not AUTH_TOKEN:
        print("Please add your Auth0 token to the script")
        sys.exit(1)
        
    headers = {
        "Authorization": f"Bearer {AUTH_TOKEN}"
    }
    
    files = {
        "file": (filename, image_bytes, "image/jpeg")
    }
    
    try:
        response = requests.post(API_URL, headers=headers, files=files)
        
        if response.status_code == 200:
            print("Receipt uploaded successfully!")
            print(f"Response: {response.json()}")
        else:
            print(f"Error uploading receipt: {response.status_code}")
            print(f"Error details: {response.text}")
            
    except Exception as e:
        print(f"Exception occurred: {e}")

if __name__ == "__main__":
    print("Creating test receipt image...")
    image_bytes = create_test_receipt_image()
    
    print("Uploading to API...")
    upload_receipt(image_bytes)
    
    print("Done!")
