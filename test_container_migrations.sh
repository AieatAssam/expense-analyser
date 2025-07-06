#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Testing database migrations with container-based testing...${NC}"

# Start test PostgreSQL container using the container fixtures
# This will run a small test script that uses the same container setup
cat << EOF > /tmp/test_container_db.py
import pytest
import time
import docker
from sqlalchemy import create_engine, text

# Container configuration (should match conftest.py)
POSTGRES_TEST_DB = "expense_test_db"
POSTGRES_TEST_USER = "expense_test_user"
POSTGRES_TEST_PASSWORD = "expense_test_password"
POSTGRES_TEST_PORT = "5433"

# Start container
client = docker.from_env()
print("Starting PostgreSQL container for migration testing...")

# Create and start the container
container = client.containers.run(
    "postgres:16",
    name="expense_test_migrations_db",
    detach=True,
    auto_remove=True,
    environment={
        "POSTGRES_USER": POSTGRES_TEST_USER,
        "POSTGRES_PASSWORD": POSTGRES_TEST_PASSWORD,
        "POSTGRES_DB": POSTGRES_TEST_DB,
    },
    ports={
        "5432/tcp": POSTGRES_TEST_PORT
    }
)

# Wait for container to be ready
print("Waiting for PostgreSQL to be ready...")
time.sleep(3)  # Initial wait

# Try to connect
max_retries = 10
retry_count = 0
connected = False

while not connected and retry_count < max_retries:
    try:
        # Create a test connection
        db_url = f"postgresql://{POSTGRES_TEST_USER}:{POSTGRES_TEST_PASSWORD}@localhost:{POSTGRES_TEST_PORT}/{POSTGRES_TEST_DB}"
        engine = create_engine(db_url)
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            connected = True
            print("Successfully connected to PostgreSQL container")
    except Exception as e:
        retry_count += 1
        print(f"Connection attempt {retry_count}/{max_retries} failed: {str(e)}")
        time.sleep(2)

if not connected:
    print("Failed to connect to PostgreSQL after multiple attempts")
    container.stop()
    exit(1)

# Print container details for alembic
print("\\nContainer ready for migration testing")
print(f"Test database URL: postgresql://{POSTGRES_TEST_USER}:{POSTGRES_TEST_PASSWORD}@localhost:{POSTGRES_TEST_PORT}/{POSTGRES_TEST_DB}")
print("\\nTo use this container with Alembic, run:")
print(f"DATABASE_URL=postgresql://{POSTGRES_TEST_USER}:{POSTGRES_TEST_PASSWORD}@localhost:{POSTGRES_TEST_PORT}/{POSTGRES_TEST_DB} alembic upgrade head")
print("\\nContainer will remain running until you stop it with:")
print("docker stop expense_test_migrations_db")

# Keep the container running
print("\\nContainer is now running for migration tests...")
EOF

# Run the Python script to start the container
python /tmp/test_container_db.py

# Check if the container started successfully
if [ $? -ne 0 ]; then
  echo -e "${RED}Failed to start PostgreSQL test container${NC}"
  exit 1
fi

# Set the environment variable for Alembic
export DATABASE_URL="postgresql://expense_test_user:expense_test_password@localhost:5433/expense_test_db"

# Run Alembic operations
echo -e "${YELLOW}Running Alembic migrations against test container...${NC}"
alembic upgrade head

# Check if migrations were successful
if [ $? -eq 0 ]; then
  echo -e "${GREEN}Migrations applied successfully!${NC}"
else
  echo -e "${RED}Migration failed!${NC}"
  docker stop expense_test_migrations_db
  exit 1
fi

# Ask if the user wants to stop the container
echo -e "${YELLOW}Migration testing complete. Do you want to stop the test container? (y/n)${NC}"
read -r answer

if [[ "$answer" == "y" || "$answer" == "Y" ]]; then
  echo "Stopping container..."
  docker stop expense_test_migrations_db
  echo -e "${GREEN}Container stopped.${NC}"
else
  echo -e "${YELLOW}Container is still running with database URL:${NC}"
  echo -e "postgresql://expense_test_user:expense_test_password@localhost:5433/expense_test_db"
  echo -e "${YELLOW}Stop it manually when done with:${NC}"
  echo -e "docker stop expense_test_migrations_db"
fi

# Clean up temporary script
rm /tmp/test_container_db.py
