#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Running all tests with container-based infrastructure...${NC}"

# Install docker package if needed
if ! pip list | grep -q "docker"; then
  echo -e "${YELLOW}Installing docker Python package...${NC}"
  pip install docker
fi

# Run pytest with coverage reporting using container-based testing
pytest --cov=app tests/ -v

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
  echo -e "${GREEN}All tests passed successfully!${NC}"
else
  echo -e "${RED}Tests failed with exit code $EXIT_CODE${NC}"
fi

exit $EXIT_CODE
