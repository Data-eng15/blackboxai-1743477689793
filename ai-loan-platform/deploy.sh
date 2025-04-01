#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color
BLUE='\033[0;34m'
YELLOW='\033[1;33m'

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

echo -e "${BLUE}Starting deployment of AI Loan Platform...${NC}\n"

# Check required commands
echo -e "${YELLOW}Checking required commands...${NC}"
REQUIRED_COMMANDS=("docker" "docker-compose" "openssl")
for cmd in "${REQUIRED_COMMANDS[@]}"; do
    if ! command_exists "$cmd"; then
        echo -e "${RED}Error: ${cmd} is not installed${NC}"
        exit 1
    fi
done
echo -e "${GREEN}All required commands are available${NC}\n"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${RED}Error: .env file not found${NC}"
    echo -e "${YELLOW}Creating .env file from example...${NC}"
    cp backend/.env.example .env
    echo -e "${RED}Please update the .env file with your production values before continuing${NC}"
    exit 1
fi

# Generate SSL certificates if they don't exist
if [ ! -f "nginx/ssl/server.crt" ] || [ ! -f "nginx/ssl/server.key" ]; then
    echo -e "${YELLOW}Generating SSL certificates...${NC}"
    cd nginx/ssl
    ./generate-certs.sh
    cd ../..
fi

# Create required directories
echo -e "${YELLOW}Creating required directories...${NC}"
mkdir -p backend/uploads backend/reports backend/logs nginx/logs

# Stop any running containers
echo -e "${YELLOW}Stopping any running containers...${NC}"
docker-compose -f docker-compose.prod.yml down

# Remove old containers, networks, and volumes
echo -e "${YELLOW}Cleaning up old deployment...${NC}"
docker-compose -f docker-compose.prod.yml rm -f
docker network prune -f

# Build and start containers
echo -e "${YELLOW}Building and starting containers...${NC}"
docker-compose -f docker-compose.prod.yml up --build -d

# Check container status
echo -e "${YELLOW}Checking container status...${NC}"
sleep 5
CONTAINERS=("loan-platform-backend-prod" "loan-platform-db-prod" "loan-platform-nginx-prod" "loan-platform-redis-prod")
ALL_RUNNING=true

for container in "${CONTAINERS[@]}"; do
    STATUS=$(docker inspect -f '{{.State.Status}}' "$container" 2>/dev/null)
    if [ "$STATUS" != "running" ]; then
        echo -e "${RED}Error: Container ${container} is not running (Status: ${STATUS})${NC}"
        ALL_RUNNING=false
    fi
done

if [ "$ALL_RUNNING" = true ]; then
    echo -e "${GREEN}All containers are running successfully${NC}"
    
    # Display container logs
    echo -e "\n${YELLOW}Container logs:${NC}"
    docker-compose -f docker-compose.prod.yml logs --tail=20
    
    echo -e "\n${GREEN}Deployment completed successfully!${NC}"
    echo -e "${BLUE}Application is now available at:${NC}"
    echo -e "  - Frontend: ${YELLOW}https://your-domain.com${NC}"
    echo -e "  - Backend API: ${YELLOW}https://your-domain.com/api${NC}"
    
    echo -e "\n${BLUE}To monitor the application:${NC}"
    echo -e "  - View logs: ${YELLOW}docker-compose -f docker-compose.prod.yml logs -f${NC}"
    echo -e "  - Check status: ${YELLOW}docker-compose -f docker-compose.prod.yml ps${NC}"
else
    echo -e "${RED}Deployment failed. Please check the logs for more information:${NC}"
    docker-compose -f docker-compose.prod.yml logs
    exit 1
fi

# Security reminder
echo -e "\n${RED}IMPORTANT SECURITY REMINDERS:${NC}"
echo -e "1. Update SSL certificates with valid ones from a trusted CA"
echo -e "2. Ensure all production secrets in .env are strong and unique"
echo -e "3. Configure proper firewall rules"
echo -e "4. Set up monitoring and alerting"
echo -e "5. Configure regular backups"
echo -e "6. Review nginx configuration for security headers"