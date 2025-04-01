#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color
BLUE='\033[0;34m'
YELLOW='\033[1;33m'

echo -e "${BLUE}Setting up AI Loan Platform Backend...${NC}\n"

# Create required directories
echo -e "${YELLOW}Creating required directories...${NC}"
mkdir -p uploads reports logs

# Create and activate virtual environment
echo -e "${YELLOW}Setting up Python virtual environment...${NC}"
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
echo -e "${YELLOW}Upgrading pip...${NC}"
pip install --upgrade pip

# Install requirements
echo -e "${YELLOW}Installing requirements...${NC}"
pip install -r requirements.txt

# Install development requirements
echo -e "${YELLOW}Installing development requirements...${NC}"
pip install pytest pytest-cov pytest-env pytest-mock coverage-badge flake8 black

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Creating .env file...${NC}"
    cp .env.example .env
    echo -e "${GREEN}Created .env file. Please update it with your configuration.${NC}"
fi

# Initialize database
echo -e "${YELLOW}Initializing database...${NC}"
export FLASK_APP=run.py
flask db upgrade

# Run tests
echo -e "${YELLOW}Running tests...${NC}"
./run_tests.sh

# Format code
echo -e "${YELLOW}Formatting code...${NC}"
black .

# Check code style
echo -e "${YELLOW}Checking code style...${NC}"
flake8 .

echo -e "\n${GREEN}Setup complete!${NC}"
echo -e "${BLUE}To start the development server:${NC}"
echo -e "1. Activate the virtual environment: ${YELLOW}source venv/bin/activate${NC}"
echo -e "2. Start the server: ${YELLOW}python run.py${NC}"
echo -e "\n${BLUE}To run tests:${NC}"
echo -e "${YELLOW}./run_tests.sh${NC}"

# Deactivate virtual environment
deactivate