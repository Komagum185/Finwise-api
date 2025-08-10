#!/bin/bash

# Finwise API Development Server Startup Script

echo "Starting Finwise API Development Server..."
echo "=========================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Creating one..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies if needed
echo "Checking dependencies..."
pip install -r requirements.txt

# Run migrations
echo "Running database migrations..."
python manage.py migrate

# Start the development server
echo "Starting Django development server..."
echo "Server will be available at: http://127.0.0.1:8000/"
echo "Admin interface: http://127.0.0.1:8000/admin/"
echo "API endpoints: http://127.0.0.1:8000/api/"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python manage.py runserver 