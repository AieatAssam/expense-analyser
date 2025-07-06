#!/bin/bash

# Test script for Alembic migration setup
# This script tests the connection to the PostgreSQL container and Alembic configuration

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Testing Alembic migration setup...${NC}"

# Check if Docker Compose is running
if ! docker-compose ps | grep -q "expense_analyser_db.*Up"; then
  echo -e "${YELLOW}Starting Docker containers...${NC}"
  docker-compose up -d db
fi

# Wait for PostgreSQL to be ready
echo -e "${YELLOW}Waiting for PostgreSQL to be ready...${NC}"
for i in {1..10}; do
  if docker-compose exec db pg_isready -U expense_user -d expense_db; then
    break
  fi
  echo "Waiting for PostgreSQL to start... ($i/10)"
  sleep 2
  if [ $i -eq 10 ]; then
    echo -e "${RED}Failed to connect to PostgreSQL container${NC}"
    exit 1
  fi
done

# Test Alembic connection
echo -e "${YELLOW}Testing Alembic connection...${NC}"
if alembic current; then
  echo -e "${GREEN}Alembic connection successful!${NC}"
else
  echo -e "${RED}Alembic connection failed!${NC}"
  echo "Check your DATABASE_URL setting and database credentials."
  exit 1
fi

echo -e "${GREEN}Alembic migration setup is working correctly!${NC}"
echo "You can now create and apply migrations."
