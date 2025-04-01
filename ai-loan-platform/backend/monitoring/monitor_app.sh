#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color
BLUE='\033[0;34m'
YELLOW='\033[1;33m'

# Configuration
LOG_DIR="logs"
REPORT_INTERVAL=3600  # 1 hour in seconds
ALERT_EMAIL="alerts@your-domain.com"
METRICS_RETENTION_DAYS=30

# Create required directories
mkdir -p "$LOG_DIR"

# Function to send email alerts
send_alert() {
    local subject="$1"
    local message="$2"
    echo "$message" | mail -s "$subject" "$ALERT_EMAIL"
}

# Function to clean old logs and reports
cleanup_old_files() {
    echo -e "${YELLOW}Cleaning up old files...${NC}"
    find "$LOG_DIR" -type f -name "*.log" -mtime +$METRICS_RETENTION_DAYS -delete
    find "$LOG_DIR" -type f -name "*.png" -mtime +$METRICS_RETENTION_DAYS -delete
    find "$LOG_DIR" -type f -name "*.html" -mtime +$METRICS_RETENTION_DAYS -delete
}

# Function to check application health
check_health() {
    local response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/api/health)
    if [ "$response" != "200" ]; then
        send_alert "Application Health Check Failed" "Health check returned status $response"
        echo -e "${RED}Health check failed: $response${NC}"
        return 1
    fi
    echo -e "${GREEN}Health check passed${NC}"
    return 0
}

# Function to monitor Docker containers
check_containers() {
    echo -e "${YELLOW}Checking Docker containers...${NC}"
    local containers=("loan-platform-backend" "loan-platform-db" "loan-platform-nginx" "loan-platform-redis")
    
    for container in "${containers[@]}"; do
        local status=$(docker inspect -f '{{.State.Status}}' "$container" 2>/dev/null)
        if [ "$status" != "running" ]; then
            send_alert "Container Down: $container" "Container $container is not running (Status: $status)"
            echo -e "${RED}Container $container is not running${NC}"
        else
            echo -e "${GREEN}Container $container is running${NC}"
        fi
    done
}

# Function to check disk space
check_disk_space() {
    echo -e "${YELLOW}Checking disk space...${NC}"
    local threshold=90
    local usage=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
    
    if [ "$usage" -gt "$threshold" ]; then
        send_alert "High Disk Usage" "Disk usage is at ${usage}%"
        echo -e "${RED}High disk usage: ${usage}%${NC}"
    else
        echo -e "${GREEN}Disk usage: ${usage}%${NC}"
    fi
}

# Function to check memory usage
check_memory() {
    echo -e "${YELLOW}Checking memory usage...${NC}"
    local threshold=85
    local usage=$(free | awk '/Mem:/ {print int($3/$2 * 100)}')
    
    if [ "$usage" -gt "$threshold" ]; then
        send_alert "High Memory Usage" "Memory usage is at ${usage}%"
        echo -e "${RED}High memory usage: ${usage}%${NC}"
    else
        echo -e "${GREEN}Memory usage: ${usage}%${NC}"
    fi
}

# Function to check CPU load
check_cpu() {
    echo -e "${YELLOW}Checking CPU load...${NC}"
    local threshold=80
    local load=$(top -bn1 | grep "Cpu(s)" | awk '{print int($2)}')
    
    if [ "$load" -gt "$threshold" ]; then
        send_alert "High CPU Load" "CPU load is at ${load}%"
        echo -e "${RED}High CPU load: ${load}%${NC}"
    else
        echo -e "${GREEN}CPU load: ${load}%${NC}"
    fi
}

# Function to generate metrics report
generate_report() {
    echo -e "${YELLOW}Generating metrics report...${NC}"
    python3 visualize.py
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Report generated successfully${NC}"
    else
        echo -e "${RED}Failed to generate report${NC}"
    fi
}

# Main monitoring loop
echo -e "${BLUE}Starting application monitoring...${NC}"

while true; do
    echo -e "\n${BLUE}Running health checks at $(date)${NC}"
    
    # Run all checks
    check_health
    check_containers
    check_disk_space
    check_memory
    check_cpu
    
    # Generate report every hour
    if [ $(($(date +%s) % REPORT_INTERVAL)) -eq 0 ]; then
        generate_report
        cleanup_old_files
    fi
    
    # Wait before next check
    sleep 60
done