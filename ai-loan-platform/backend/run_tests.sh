#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color
BLUE='\033[0;34m'
YELLOW='\033[1;33m'

echo -e "${BLUE}Starting test suite...${NC}\n"

# Create and activate virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install requirements
echo -e "${YELLOW}Installing requirements...${NC}"
pip install -r requirements.txt
pip install pytest pytest-cov pytest-env pytest-mock

# Clean up previous coverage data
echo -e "${YELLOW}Cleaning up previous coverage data...${NC}"
coverage erase

# Run tests with coverage
echo -e "${YELLOW}Running tests with coverage...${NC}\n"
pytest \
    --verbose \
    --cov=backend \
    --cov-report=term-missing \
    --cov-report=html \
    --no-cov-on-fail \
    tests/

# Check exit status
if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}All tests passed!${NC}"
else
    echo -e "\n${RED}Some tests failed!${NC}"
fi

# Generate coverage badge
coverage-badge -o coverage.svg

echo -e "\n${BLUE}Coverage report generated in htmlcov/index.html${NC}"
echo -e "${BLUE}Coverage badge generated as coverage.svg${NC}"

# Deactivate virtual environment
deactivate