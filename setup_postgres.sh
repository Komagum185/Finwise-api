#!/bin/bash

# Finwise PostgreSQL Setup Script

echo "Setting up PostgreSQL for Finwise API..."
echo "========================================"

# Check if PostgreSQL is running
if ! pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
    echo "PostgreSQL is not running. Please start PostgreSQL first."
    echo "You can start it with: brew services start postgresql"
    exit 1
fi

echo "PostgreSQL is running. Creating database and user..."

# Create database and user
psql -h localhost -U postgres -c "CREATE DATABASE finwise_db;" 2>/dev/null || echo "Database already exists or using different user"
psql -h localhost -U postgres -c "CREATE USER finwise_user WITH PASSWORD 'finwise_password';" 2>/dev/null || echo "User already exists or using different user"
psql -h localhost -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE finwise_db TO finwise_user;" 2>/dev/null || echo "Privileges already granted or using different user"
psql -h localhost -U postgres -c "ALTER USER finwise_user CREATEDB;" 2>/dev/null || echo "User privileges already set or using different user"

echo "PostgreSQL setup completed!"
echo ""
echo "Database: finwise_db"
echo "User: finwise_user"
echo "Password: finwise_password"
echo ""
echo "You can now run: python manage.py migrate" 