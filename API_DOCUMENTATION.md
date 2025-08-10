# Finwise API Documentation

## Overview

The Finwise API is a comprehensive financial management system built with Django REST Framework and PostgreSQL. It provides endpoints for managing transactions, budgets, goals, categories, and user profiles with JWT authentication.

## Base URL

```
http://127.0.0.1:8000/api/
```

## Authentication

The API uses JWT (JSON Web Tokens) for authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your_access_token>
```

### Authentication Endpoints

#### Register User

```
POST /api/auth/register/
```

**Request Body:**

```json
{
    "username": "john_doe",
    "email": "john@example.com",
    "password": "secure_password",
    "first_name": "John",
    "last_name": "Doe",
    "phone_number": "+1234567890",
    "default_currency": "USD",
    "monthly_income": "5000.00"
}
```

#### Login

```
POST /api/auth/login/
```

**Request Body:**

```json
{
    "username": "john_doe",
    "password": "secure_password"
}
```

**Response:**

```json
{
    "message": "Login successful",
    "user": {...},
    "tokens": {
        "refresh": "refresh_token_here",
        "access": "access_token_here"
    }
}
```

#### Refresh Token

```
POST /api/auth/token/refresh/
```

**Request Body:**

```json
{
    "refresh": "refresh_token_here"
}
```

#### Logout

```
POST /api/auth/logout/
```

**Request Body:**

```json
{
    "refresh_token": "refresh_token_here"
}
```

## Core Endpoints

### Categories

#### List Categories

```
GET /api/categories/
```

#### Create Category

```
POST /api/categories/
```

**Request Body:**

```json
{
    "name": "Groceries",
    "description": "Food and household items",
    "category_type": "expense",
    "icon": "🛒",
    "color": "#dc3545"
}
```

#### Get Category Analytics

```
GET /api/categories/{id}/analytics/
```

**Query Parameters:**

- `start_date`: YYYY-MM-DD
- `end_date`: YYYY-MM-DD

### Transactions

#### List Transactions

```
GET /api/transactions/
```

**Query Parameters:**

- `transaction_type`: income, expense, transfer
- `category`: category_id
- `status`: pending, completed, cancelled
- `date`: YYYY-MM-DD
- `search`: search in description, notes, location
- `ordering`: date, amount, created_at

#### Create Transaction

```
POST /api/transactions/
```

**Request Body:**

```json
{
    "amount": "150.00",
    "description": "Grocery shopping",
    "transaction_type": "expense",
    "category": 1,
    "date": "2024-01-15",
    "status": "completed",
    "notes": "Weekly groceries",
    "location": "Walmart",
    "tags": ["groceries", "weekly"]
}
```

#### Get Financial Summary

```
GET /api/transactions/summary/
```

**Query Parameters:**

- `start_date`: YYYY-MM-DD
- `end_date`: YYYY-MM-DD

**Response:**

```json
{
    "period": {"start_date": "2024-01-01", "end_date": "2024-01-31"},
    "total_income": "5000.00",
    "total_expenses": "3200.00",
    "net_balance": "1800.00",
    "category_breakdown": [...],
    "recent_transactions": [...],
    "budget_status": [...],
    "goal_progress": [...]
}
```

#### Get Analytics

```
GET /api/transactions/analytics/
```

### Budgets

#### List Budgets

```
GET /api/budgets/
```

#### Create Budget

```
POST /api/budgets/
```

**Request Body:**

```json
{
    "category": 1,
    "amount": "500.00",
    "period": "monthly",
    "start_date": "2024-01-01",
    "end_date": "2024-01-31"
}
```

#### Get Budget Overview

```
GET /api/budgets/overview/
```

#### Adjust Budget Amount

```
POST /api/budgets/{id}/adjust_amount/
```

**Request Body:**

```json
{
    "amount": "600.00"
}
```

### Goals

#### List Goals

```
GET /api/goals/
```

#### Create Goal

```
POST /api/goals/
```

**Request Body:**

```json
{
    "name": "Emergency Fund",
    "description": "Save 6 months of expenses",
    "goal_type": "savings",
    "target_amount": "15000.00",
    "current_amount": "5000.00",
    "target_date": "2024-12-31",
    "priority": 1
}
```

#### Update Goal Progress

```
POST /api/goals/{id}/update_progress/
```

**Request Body:**

```json
{
    "current_amount": "7500.00"
}
```

#### Get Progress Summary

```
GET /api/goals/progress_summary/
```

### User Profiles

#### Get Profile

```
GET /api/profiles/
```

#### Update Profile

```
PUT /api/profiles/
```

**Request Body:**

```json
{
    "currency": "USD",
    "monthly_income": "6000.00",
    "emergency_fund_target": "18000.00",
    "notification_preferences": {
        "budget_alerts": true,
        "goal_reminders": true
    },
    "financial_goals": "Save for house down payment"
}
```

#### Get Dashboard

```
GET /api/profiles/dashboard/
```

### Recurring Transactions

#### List Recurring Transactions

```
GET /api/recurring-transactions/
```

#### Create Recurring Transaction

```
POST /api/recurring-transactions/
```

**Request Body:**

```json
{
    "description": "Netflix Subscription",
    "amount": "15.99",
    "transaction_type": "expense",
    "category": 1,
    "frequency": "monthly",
    "start_date": "2024-01-01",
    "next_due_date": "2024-02-01"
}
```

#### Get Upcoming Transactions

```
GET /api/recurring-transactions/upcoming/
```

#### Process Recurring Transaction

```
POST /api/recurring-transactions/{id}/process/
```

## Data Models

### Transaction

- `id`: UUID (primary key)
- `user`: ForeignKey to User
- `amount`: Decimal (max 10 digits, 2 decimal places)
- `description`: CharField (max 255)
- `transaction_type`: ChoiceField (income, expense, transfer)
- `category`: ForeignKey to Category
- `date`: DateField
- `status`: ChoiceField (pending, completed, cancelled)
- `notes`: TextField
- `receipt_image`: ImageField
- `location`: CharField (max 200)
- `tags`: JSONField
- `created_at`: DateTimeField
- `updated_at`: DateTimeField

### Category

- `id`: AutoField (primary key)
- `name`: CharField (max 100, unique)
- `description`: TextField
- `category_type`: ChoiceField (income, expense, both)
- `icon`: CharField (max 50)
- `color`: CharField (max 7)
- `is_active`: BooleanField
- `created_at`: DateTimeField
- `updated_at`: DateTimeField

### Budget

- `id`: AutoField (primary key)
- `user`: ForeignKey to User
- `category`: ForeignKey to Category
- `amount`: Decimal (max 10 digits, 2 decimal places)
- `period`: ChoiceField (monthly, yearly, weekly)
- `start_date`: DateField
- `end_date`: DateField
- `is_active`: BooleanField
- `created_at`: DateTimeField
- `updated_at`: DateTimeField

### Goal

- `id`: AutoField (primary key)
- `user`: ForeignKey to User
- `name`: CharField (max 200)
- `description`: TextField
- `goal_type`: ChoiceField (savings, debt_payoff, investment, purchase, emergency_fund)
- `target_amount`: Decimal (max 12 digits, 2 decimal places)
- `current_amount`: Decimal (max 12 digits, 2 decimal places)
- `target_date`: DateField
- `status`: ChoiceField (active, completed, paused, cancelled)
- `priority`: IntegerField (1-5)
- `created_at`: DateTimeField
- `updated_at`: DateTimeField

## Business Logic Features

### Automatic Calculations

- Budget spent amount and remaining amount
- Goal progress percentage and remaining amount
- Financial summaries with category breakdowns
- Monthly trends and analytics

### Validation Rules

- Transaction amounts must be positive
- Category types must match transaction types
- Budget periods cannot overlap
- Goal current amount cannot exceed target amount
- Completed transactions cannot have future dates

### Smart Features

- Automatic goal status updates when completed
- Budget alerts when spending exceeds thresholds
- Goal reminders for approaching deadlines
- Recurring transaction processing

## Error Handling

The API returns appropriate HTTP status codes and error messages:

- `400 Bad Request`: Validation errors
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Permission denied
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server errors

## Rate Limiting

- Anonymous users: 100 requests per day
- Authenticated users: 1000 requests per day

## Testing

To test the API:

1. Start the server: `python manage.py runserver`
2. Use tools like Postman, curl, or the Django admin interface
3. Register a user and get JWT tokens
4. Include the access token in the Authorization header for protected endpoints

## Example Usage

```bash
# Register a user
curl -X POST http://127.0.0.1:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","email":"test@example.com","password":"testpass123","first_name":"Test","last_name":"User"}'

# Login and get tokens
curl -X POST http://127.0.0.1:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"testpass123"}'

# Create a transaction (with token)
curl -X POST http://127.0.0.1:8000/api/transactions/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"amount":"100.00","description":"Test transaction","transaction_type":"expense","category":1,"date":"2024-01-15"}'
```
