#!/bin/bash
# Run tests in the virtual environment

# Activate virtual environment
source venv/bin/activate

# Run tests
echo "Running MissionMind TasksMind tests..."
pytest -v