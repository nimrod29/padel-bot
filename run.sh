#!/bin/bash

# Padel Monitor Startup Script
# This script activates the virtual environment and runs the padel monitor

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🎾 Padel Game Monitor${NC}"
echo -e "${GREEN}========================${NC}"

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv .venv
    
    echo -e "${YELLOW}Installing dependencies...${NC}"
    source .venv/bin/activate
    pip install -r requirements.txt
fi

# Activate virtual environment
source .venv/bin/activate

# Check if configuration is needed
if grep -q "YOUR_BOT_TOKEN_HERE" config.py; then
    echo -e "${YELLOW}⚠️  Configuration needed!${NC}"
    echo -e "${YELLOW}Please update your Telegram bot token and chat ID in config.py${NC}"
    echo -e "${YELLOW}Run: python main.py --mode config for help${NC}"
    echo ""
fi

# Run the application with provided arguments, or default to monitor mode
if [ $# -eq 0 ]; then
    echo -e "${GREEN}Starting continuous monitoring...${NC}"
    echo -e "${GREEN}Press Ctrl+C to stop${NC}"
    echo ""
    python main.py
else
    python main.py "$@"
fi 