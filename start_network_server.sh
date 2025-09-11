#!/bin/bash

# School Upgrade System Network Server
# This script starts the server with network access enabled

echo "🏫 Balochistan School Upgrade System"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Activate virtual environment if it exists
if [ -d "../.venv" ]; then
    echo -e "${BLUE}📦 Activating virtual environment...${NC}"
    source ../.venv/bin/activate
elif [ -d ".venv" ]; then
    echo -e "${BLUE}📦 Activating virtual environment...${NC}"
    source .venv/bin/activate
else
    echo -e "${YELLOW}⚠️  No virtual environment found, using system Python${NC}"
fi

# Get IP address
IP_ADDRESS=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -n1)

echo -e "${GREEN}✅ Server starting...${NC}"
echo -e "${BLUE}📍 Local access: http://127.0.0.1:5010${NC}"
echo -e "${BLUE}🌐 Network access: http://$IP_ADDRESS:5010${NC}"
echo -e "${YELLOW}📱 Use the network URL on other devices${NC}"
echo -e "${RED}🛑 Press Ctrl+C to stop${NC}"
echo "=================================="

# Start the server
python app.py
