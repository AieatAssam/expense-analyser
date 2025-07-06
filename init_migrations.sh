#!/bin/bash

# Script to initialize Alembic migrations structure
# This script is part of Task 1.4: Configure Alembic for Database Migrations

# Function to handle errors
handle_error() {
  echo "ERROR: $1"
  exit 1
}

# Create migrations directory structure if it doesn't exist
echo "Creating migrations directory structure..."
mkdir -p migrations/versions || handle_error "Failed to create migrations directory"

echo "Alembic migration system is now configured."
echo ""
echo "To create your first migration, run:"
echo "  alembic revision --autogenerate -m \"initial\""
echo ""
echo "To apply migrations, run:"
echo "  alembic upgrade head"
echo ""
echo "To check current migration status, run:"
echo "  alembic current"
echo ""
echo "For a Docker-based approach, you can use:"
echo "  docker-compose exec api alembic revision --autogenerate -m \"initial\""
echo "  docker-compose exec api alembic upgrade head"
