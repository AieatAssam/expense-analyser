#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Starting PostgreSQL test container and running tests...${NC}"

# Check if docker-py is installed
if ! pip list | grep -q "docker"; then
  echo -e "${YELLOW}Installing docker Python package...${NC}"
  pip install docker
fi

# Run pytest with container-based database
# This will automatically start the container via the postgres_container fixture
pytest "$@"

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
  echo -e "${GREEN}Tests completed successfully!${NC}"
else
  echo -e "${RED}Tests failed with exit code $EXIT_CODE${NC}"
fi

exit $EXIT_CODE
