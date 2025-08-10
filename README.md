# Finwise API

A Django-based REST API for financial management and planning with PostgreSQL database.

## Setup

### Prerequisites
- Python 3.8 or higher
- pip
- PostgreSQL (already installed)

### Installation

#### Option 1: Automated Setup (Recommended)
```bash
# Run the complete setup script
./setup_project.sh
```

#### Option 2: Manual Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd Finwise-api
```

2. Create and activate a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up PostgreSQL database:
```bash
./setup_postgres.sh
```

5. Run database migrations:
```bash
python manage.py migrate
```

6. Create a superuser:
```bash
python manage.py createsuperuser
```

7. Run the development server:
```bash
python manage.py runserver
```

The API will be available at `http://127.0.0.1:8000/`

## Project Structure

```
Finwise-api/
├── api/                 # Main API app with financial models
├── users/              # Custom user management app
├── finwise/            # Django project settings
├── manage.py           # Django management script
├── requirements.txt    # Python dependencies
├── .env                # Environment variables
├── setup_project.sh    # Automated setup script
├── setup_postgres.sh   # PostgreSQL setup script
├── API_DOCUMENTATION.md # Complete API documentation
├── .gitignore         # Git ignore patterns
└── README.md          # This file
```

## Development

### Adding new apps
```bash
python manage.py startapp your_app_name
```

### Making migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### Running tests
```bash
python manage.py test
```

## Features

- **JWT Authentication**: Secure token-based authentication
- **Comprehensive Financial Models**: Transactions, budgets, goals, categories
- **Advanced Analytics**: Financial summaries, spending trends, budget tracking
- **Data Validation**: Robust business logic and validation rules
- **PostgreSQL Database**: Production-ready database with proper indexing
- **RESTful API**: Complete CRUD operations for all models
- **File Uploads**: Receipt images and profile pictures
- **Recurring Transactions**: Automated transaction processing
- **User Profiles**: Extended user information and preferences

## API Documentation

Complete API documentation is available in `API_DOCUMENTATION.md`.

### Quick Start

1. **Register a user:**
```bash
curl -X POST http://127.0.0.1:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","email":"test@example.com","password":"testpass123","first_name":"Test","last_name":"User"}'
```

2. **Login and get tokens:**
```bash
curl -X POST http://127.0.0.1:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"testpass123"}'
```

3. **Create a transaction:**
```bash
curl -X POST http://127.0.0.1:8000/api/transactions/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"amount":"100.00","description":"Test transaction","transaction_type":"expense","category":1,"date":"2024-01-15"}'
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License. 