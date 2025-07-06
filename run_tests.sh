#!/bin/bash

# Check if docker package is installed
if ! pip list | grep -q "docker"; then
    echo "Installing docker package for container tests..."
    pip install docker
fi

# Run pytest with coverage reporting
pytest --cov=app tests/ -v "$@"
