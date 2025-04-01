#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color
BLUE='\033[0;34m'
YELLOW='\033[1;33m'

echo -e "${BLUE}Initializing database migrations...${NC}\n"

# Check if virtual environment exists
if [ ! -d "../venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv ../venv
fi

# Activate virtual environment
source ../venv/bin/activate

# Install required packages
echo -e "${YELLOW}Installing required packages...${NC}"
pip install flask-migrate flask-script psycopg2-binary

# Initialize migrations
echo -e "${YELLOW}Initializing Flask-Migrate...${NC}"
export FLASK_APP=../run.py
flask db init

# Create first migration
echo -e "${YELLOW}Creating initial migration...${NC}"
flask db migrate -m "Initial migration"

# Apply migration
echo -e "${YELLOW}Applying migration...${NC}"
flask db upgrade

# Create admin user
echo -e "${YELLOW}Creating admin user...${NC}"
python manage_db.py create_admin

echo -e "\n${GREEN}Database migrations initialized successfully!${NC}"
echo -e "${BLUE}Available commands:${NC}"
echo -e "  - Create new migration: ${YELLOW}flask db migrate -m \"your message\"${NC}"
echo -e "  - Apply migrations: ${YELLOW}flask db upgrade${NC}"
echo -e "  - Rollback migration: ${YELLOW}flask db downgrade${NC}"
echo -e "  - View migration status: ${YELLOW}flask db current${NC}"
echo -e "  - View migration history: ${YELLOW}flask db history${NC}"
echo -e "\n${BLUE}Database management commands:${NC}"
echo -e "  - Create tables: ${YELLOW}python manage_db.py create_db${NC}"
echo -e "  - Drop tables: ${YELLOW}python manage_db.py drop_db${NC}"
echo -e "  - Reset tables: ${YELLOW}python manage_db.py reset_db${NC}"
echo -e "  - Create admin: ${YELLOW}python manage_db.py create_admin${NC}"
echo -e "  - Backup database: ${YELLOW}python manage_db.py backup_db${NC}"
echo -e "  - Restore database: ${YELLOW}python manage_db.py restore_db${NC}"
echo -e "  - Seed database: ${YELLOW}python manage_db.py seed_db${NC}"

# Deactivate virtual environment
deactivate