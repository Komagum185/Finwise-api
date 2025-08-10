#!/bin/bash

# Finwise API Project Setup Script

echo "Setting up Finwise API Project..."
echo "================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Check if PostgreSQL is running
echo "Checking PostgreSQL status..."
if ! pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
    echo "PostgreSQL is not running. Please start PostgreSQL first."
    echo "You can start it with: brew services start postgresql"
    exit 1
fi

echo "PostgreSQL is running. Setting up database..."

# Try to create database and user (this might fail if they already exist)
echo "Creating database and user..."
psql -h localhost -U postgres -c "CREATE DATABASE finwise_db;" 2>/dev/null || echo "Database already exists or using different user"
psql -h localhost -U postgres -c "CREATE USER finwise_user WITH PASSWORD 'finwise_password';" 2>/dev/null || echo "User already exists or using different user"
psql -h localhost -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE finwise_db TO finwise_user;" 2>/dev/null || echo "Privileges already granted or using different user"
psql -h localhost -U postgres -c "ALTER USER finwise_user CREATEDB;" 2>/dev/null || echo "User privileges already set or using different user"

# Run migrations
echo "Running Django migrations..."
python manage.py migrate

# Create superuser if it doesn't exist
echo "Creating superuser..."
python manage.py createsuperuser --username admin --email admin@finwise.com --noinput

# Set admin password
echo "Setting admin password..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
admin_user = User.objects.get(username='admin')
admin_user.set_password('admin123')
admin_user.save()
print('Admin user created with password: admin123')
"

echo ""
echo "=========================================="
echo "Setup completed successfully!"
echo "=========================================="
echo ""
echo "Database: finwise_db"
echo "User: finwise_user"
echo "Password: finwise_password"
echo ""
echo "Django Admin:"
echo "Username: admin"
echo "Password: admin123"
echo ""
echo "To start the server:"
echo "source venv/bin/activate"
echo "python manage.py runserver"
echo ""
echo "API endpoints:"
echo "- http://127.0.0.1:8000/api/"
echo "- http://127.0.0.1:8000/admin/"
echo "- http://127.0.0.1:8000/api/auth/" 