#!/bin/bash
# Run the FastAPI server in the virtual environment

# Activate virtual environment
source venv/bin/activate

# Load environment variables from .env file
set -a
source .env
set +a

# Safety check: Ensure we're using PostgreSQL
if [[ ! "$DATABASE_URL" =~ ^postgresql:// ]]; then
    echo "❌ ERROR: DATABASE_URL must be a PostgreSQL connection string"
    echo "Current value: $DATABASE_URL"
    exit 1
fi

# Run the server
echo "Starting MissionMind TasksMind server..."
echo "Using database: ${DATABASE_URL%%@*}@****" # Hide password in output
uvicorn app.main:app --reload --port 8000