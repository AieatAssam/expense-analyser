#!/bin/bash
# Apply migrations for receipt image storage changes

# Set up Python venv if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv .venv
fi

# Activate the virtual environment
source .venv/bin/activate

# Ensure Alembic is installed
pip install alembic

# Run the migration
echo "Applying migration for receipt image storage changes..."
alembic upgrade head

echo "Migration complete!"
