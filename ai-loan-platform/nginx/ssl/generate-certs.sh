#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color
BLUE='\033[0;34m'
YELLOW='\033[1;33m'

echo -e "${BLUE}Generating self-signed SSL certificates for development...${NC}\n"

# Create SSL directory if it doesn't exist
mkdir -p /etc/nginx/ssl

# Generate private key
echo -e "${YELLOW}Generating private key...${NC}"
openssl genrsa -out server.key 2048

# Generate CSR
echo -e "${YELLOW}Generating Certificate Signing Request...${NC}"
openssl req -new -key server.key -out server.csr -subj "/C=IN/ST=State/L=City/O=Organization/CN=localhost"

# Generate self-signed certificate
echo -e "${YELLOW}Generating self-signed certificate...${NC}"
openssl x509 -req -days 365 -in server.csr -signkey server.key -out server.crt

# Move files to appropriate location
echo -e "${YELLOW}Moving certificates to nginx/ssl directory...${NC}"
mv server.crt server.key /etc/nginx/ssl/

# Clean up
rm server.csr

# Set permissions
chmod 600 /etc/nginx/ssl/server.key
chmod 644 /etc/nginx/ssl/server.crt

echo -e "\n${GREEN}SSL certificates generated successfully!${NC}"
echo -e "${BLUE}Location:${NC}"
echo -e "  - Private key: ${YELLOW}/etc/nginx/ssl/server.key${NC}"
echo -e "  - Certificate: ${YELLOW}/etc/nginx/ssl/server.crt${NC}"
echo -e "\n${RED}Note: These are self-signed certificates for development only.${NC}"
echo -e "${RED}Do not use them in production!${NC}"