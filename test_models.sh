#!/bin/bash

# Check if docker package is installed
if ! pip list | grep -q "docker"; then
    echo "Installing docker package for container tests..."
    pip install docker
fi

# Run container-based model tests
echo "Running model tests with container-based PostgreSQL database..."
pytest -xvs tests/test_models.py
