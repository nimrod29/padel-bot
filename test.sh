#!/bin/bash

# Test script for Padel Monitor
# Usage: ./test.sh [date]
# Example: ./test.sh 2025-11-27

cd /Users/nmrwdsny/projects/padel_times

# Load environment variables from .env file if it exists
if [ -f .env ]; then
    echo "Loading environment variables from .env file..."
    export $(grep -v '^#' .env | xargs)
fi

# Activate virtual environment
source .venv/bin/activate

# Run the test
if [ -z "$1" ]; then
    # No date provided, run for today
    python main.py --mode single
else
    # Date provided, use it
    python main.py --mode single --date "$1"
fi

