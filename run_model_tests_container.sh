#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Setting up test environment...${NC}"

# Install docker package if needed
if ! pip list | grep -q "docker"; then
  echo -e "${YELLOW}Installing docker Python package...${NC}"
  pip install docker
fi

# Add docker to requirements.txt if not already there
if ! grep -q "^docker" requirements.txt; then
  echo -e "${YELLOW}Adding docker package to requirements.txt...${NC}"
  echo "docker" >> requirements.txt
fi

# Run pytest for model tests specifically with container
echo -e "${YELLOW}Running model tests with PostgreSQL container...${NC}"
pytest tests/test_models.py -v

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
  echo -e "${GREEN}Model tests completed successfully!${NC}"
else
  echo -e "${RED}Model tests failed with exit code $EXIT_CODE${NC}"
  exit $EXIT_CODE
fi
