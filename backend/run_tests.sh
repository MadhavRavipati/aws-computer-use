#!/bin/bash
# ABOUTME: Test runner script for backend Python tests
# ABOUTME: Runs pytest with coverage and generates reports

set -e

echo "Running backend tests..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Run tests with coverage
echo "Running tests with coverage..."
pytest -v --cov=agents --cov=functions --cov=vnc_bridge --cov-report=html --cov-report=term-missing

# Check if tests passed
if [ $? -eq 0 ]; then
    echo "✅ All tests passed!"
    echo "Coverage report generated at: htmlcov/index.html"
else
    echo "❌ Tests failed!"
    exit 1
fi