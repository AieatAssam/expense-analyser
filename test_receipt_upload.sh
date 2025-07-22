#!/bin/bash
# Run tests for receipt upload functionality

# Set up Python venv if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv .venv
fi

# Activate the virtual environment
source .venv/bin/activate

# Install or update dependencies
pip install -r requirements.txt

# Run pytest for receipt upload tests
pytest tests/test_receipt_upload.py -v
