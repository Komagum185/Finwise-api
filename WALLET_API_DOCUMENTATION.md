# Enhanced Wallet API Documentation

This document describes the enhanced wallet system that matches the TypeScript interfaces provided. The system provides comprehensive wallet management capabilities for MSEs (Micro and Small Enterprises).

## Overview

The enhanced wallet system includes:
- **EnhancedWallet**: Main wallet model with MSE integration
- **EnhancedWalletTransaction**: Transaction tracking with full categorization
- **WalletTransfer**: Inter-wallet transfer functionality
- **WalletStatistics**: Aggregated wallet statistics and reporting

## API Endpoints

### Base URL
```
/api/wallet/
```

## 1. Enhanced Wallets

### Get All Wallets
```http
GET /api/wallet/enhanced-wallets/
```

**Response:**
```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "1",
      "mse_id": "MSE001",
      "mse_name": "ABC Business",
      "mse_code": "ABC",
      "account_number": "ACC001",
      "account_type": "Business",
      "balance": "1500.00",
      "currency": "USD",
      "status": "Active",
      "last_transaction": "2024-01-15T10:30:00Z",
      "description": "Main business account",
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-15T10:30:00Z",
      "transaction_count": 25,
      "monthly_volume": "5000.00"
    }
  ]
}
```

### Get Wallet by ID
```http
GET /api/wallet/enhanced-wallets/{id}/
```

### Create New Wallet
```http
POST /api/wallet/enhanced-wallets/
```

**Request Body:**
```json
{
  "mse_id": "MSE002",
  "mse_name": "XYZ Enterprise",
  "mse_code": "XYZ",
  "account_number": "ACC002",
  "account_type": "Savings",
  "currency": "USD",
  "description": "Savings account for future investments"
}
```

### Update Wallet Status
```http
POST /api/wallet/enhanced-wallets/{id}/update_status/
```

**Request Body:**
```json
{
  "status": "Suspended"
}
```

### Get Wallet Balance
```http
GET /api/wallet/enhanced-wallets/{id}/balance/
```

**Response:**
```json
{
  "wallet_id": "1",
  "mse_name": "ABC Business",
  "account_number": "ACC001",
  "balance": "1500.00",
  "currency": "USD",
  "status": "Active"
}
```

### Get Account Types
```http
GET /api/wallet/enhanced-wallets/account_types/
```

**Response:**
```json
[
  {"value": "Business", "label": "Business"},
  {"value": "Savings", "label": "Savings"},
  {"value": "Investment", "label": "Investment"},
  {"value": "Emergency", "label": "Emergency"}
]
```

### Get Wallet Statuses
```http
GET /api/wallet/enhanced-wallets/statuses/
```

**Response:**
```json
[
  {"value": "Active", "label": "Active"},
  {"value": "Inactive", "label": "Inactive"},
  {"value": "Suspended", "label": "Suspended"},
  {"value": "Pending", "label": "Pending"}
]
```

## 2. Enhanced Wallet Transactions

### Get All Transactions
```http
GET /api/wallet/enhanced-wallet-transactions/
```

**Response:**
```json
{
  "count": 3,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "type": "Credit",
      "amount": "500.00",
      "description": "Payment received for services",
      "date": "2024-01-15T10:30:00Z",
      "status": "Completed",
      "reference": "PAY001",
      "category": "Payment",
      "related_transaction_id": null
    }
  ]
}
```

### Create Transaction
```http
POST /api/wallet/enhanced-wallet-transactions/create_transaction/
```

**Request Body:**
```json
{
  "wallet_id": "1",
  "type": "Credit",
  "amount": "100.00",
  "description": "Cash deposit",
  "category": "Deposit",
  "reference": "DEP001"
}
```

### Get Transaction Types
```http
GET /api/wallet/enhanced-wallet-transactions/transaction_types/
```

**Response:**
```json
[
  {"value": "Credit", "label": "Credit"},
  {"value": "Debit", "label": "Debit"},
  {"value": "Transfer", "label": "Transfer"},
  {"value": "Withdrawal", "label": "Withdrawal"},
  {"value": "Deposit", "label": "Deposit"}
]
```

### Get Transaction Categories
```http
GET /api/wallet/enhanced-wallet-transactions/categories/
```

**Response:**
```json
[
  {"value": "Payment", "label": "Payment"},
  {"value": "Purchase", "label": "Purchase"},
  {"value": "Sale", "label": "Sale"},
  {"value": "Transfer", "label": "Transfer"},
  {"value": "Fee", "label": "Fee"},
  {"value": "Refund", "label": "Refund"}
]
```

### Get Transaction Summary
```http
GET /api/wallet/enhanced-wallet-transactions/summary/
```

**Response:**
```json
{
  "total_balance": "2500.00",
  "total_wallets": 2,
  "active_wallets": 2,
  "monthly_volume": "7500.00",
  "monthly_transactions": 15,
  "currency": "USD"
}
```

## 3. Wallet Transfers

### Get All Transfers
```http
GET /api/wallet/wallet-transfers/
```

**Response:**
```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "from_wallet_id": "1",
      "to_wallet_id": "2",
      "amount": "200.00",
      "description": "Transfer to savings account",
      "currency": "USD"
    }
  ]
}
```

### Execute Transfer
```http
POST /api/wallet/wallet-transfers/execute_transfer/
```

**Request Body:**
```json
{
  "from_wallet_id": "1",
  "to_wallet_id": "2",
  "amount": "200.00",
  "description": "Transfer to savings account",
  "currency": "USD"
}
```

## 4. Wallet Statistics

### Get All Statistics
```http
GET /api/wallet/wallet-statistics/
```

### Get Overview Statistics
```http
GET /api/wallet/wallet-statistics/overview/
```

**Response:**
```json
{
  "total_balance": "2500.00",
  "total_wallets": 2,
  "active_wallets": 2,
  "monthly_volume": "7500.00",
  "monthly_transactions": 15,
  "currency": "USD"
}
```

## 5. Filtering and Search

### Filter Wallets
```http
GET /api/wallet/enhanced-wallets/?status=Active&account_type=Business&currency=USD
```

### Search Wallets
```http
GET /api/wallet/enhanced-wallets/?search=ABC
```

### Filter Transactions
```http
GET /api/wallet/enhanced-wallet-transactions/?type=Credit&status=Completed&category=Payment
```

### Date Range Filtering
```http
GET /api/wallet/enhanced-wallet-transactions/?date__gte=2024-01-01&date__lte=2024-01-31
```

## 6. Data Models

### EnhancedWallet Model
```python
class EnhancedWallet(models.Model):
    ACCOUNT_TYPES = [
        ('Business', 'Business'),
        ('Savings', 'Savings'),
        ('Investment', 'Investment'),
        ('Emergency', 'Emergency'),
    ]
    
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
        ('Suspended', 'Suspended'),
        ('Pending', 'Pending'),
    ]
    
    mse_id = models.CharField(max_length=100)
    mse_name = models.CharField(max_length=200)
    mse_code = models.CharField(max_length=50)
    account_number = models.CharField(max_length=100, unique=True)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES)
    balance = models.DecimalField(max_digits=20, decimal_places=2, default=0.00)
    currency = models.CharField(max_length=3, default='USD')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    description = models.TextField(blank=True)
    last_transaction = models.DateTimeField(null=True, blank=True)
    transaction_count = models.IntegerField(default=0)
    monthly_volume = models.DecimalField(max_digits=20, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### EnhancedWalletTransaction Model
```python
class EnhancedWalletTransaction(models.Model):
    TRANSACTION_TYPES = [
        ('Credit', 'Credit'),
        ('Debit', 'Debit'),
        ('Transfer', 'Transfer'),
        ('Withdrawal', 'Withdrawal'),
        ('Deposit', 'Deposit'),
    ]
    
    STATUS_CHOICES = [
        ('Completed', 'Completed'),
        ('Pending', 'Pending'),
        ('Failed', 'Failed'),
        ('Cancelled', 'Cancelled'),
    ]
    
    CATEGORY_CHOICES = [
        ('Payment', 'Payment'),
        ('Purchase', 'Purchase'),
        ('Sale', 'Sale'),
        ('Transfer', 'Transfer'),
        ('Fee', 'Fee'),
        ('Refund', 'Refund'),
    ]
    
    wallet = models.ForeignKey(EnhancedWallet, on_delete=models.CASCADE)
    type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    description = models.TextField()
    date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    reference = models.CharField(max_length=100, blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, blank=True)
    related_transaction_id = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

## 7. Usage Examples

### Creating a New Wallet
```python
import requests

# Create a new wallet
wallet_data = {
    "mse_id": "MSE003",
    "mse_name": "New Business",
    "mse_code": "NEW",
    "account_number": "ACC003",
    "account_type": "Business",
    "currency": "USD",
    "description": "Main business account"
}

response = requests.post(
    "http://localhost:8000/api/wallet/enhanced-wallets/",
    json=wallet_data,
    headers={"Authorization": "Bearer YOUR_TOKEN"}
)

if response.status_code == 201:
    wallet = response.json()
    print(f"Created wallet: {wallet['account_number']}")
```

### Making a Transaction
```python
# Create a transaction
transaction_data = {
    "wallet_id": "1",
    "type": "Credit",
    "amount": "250.00",
    "description": "Payment for services rendered",
    "category": "Payment",
    "reference": "PAY002"
}

response = requests.post(
    "http://localhost:8000/api/wallet/enhanced-wallet-transactions/create_transaction/",
    json=transaction_data,
    headers={"Authorization": "Bearer YOUR_TOKEN"}
)

if response.status_code == 201:
    transaction = response.json()
    print(f"Transaction created: {transaction['id']}")
```

### Transferring Between Wallets
```python
# Execute a transfer
transfer_data = {
    "from_wallet_id": "1",
    "to_wallet_id": "2",
    "amount": "100.00",
    "description": "Monthly savings transfer",
    "currency": "USD"
}

response = requests.post(
    "http://localhost:8000/api/wallet/wallet-transfers/execute_transfer/",
    json=transfer_data,
    headers={"Authorization": "Bearer YOUR_TOKEN"}
)

if response.status_code == 201:
    transfer = response.json()
    print(f"Transfer completed: {transfer['id']}")
```

## 8. Error Handling

### Common Error Responses

**400 Bad Request:**
```json
{
  "error": "Insufficient balance in source wallet"
}
```

**404 Not Found:**
```json
{
  "error": "Wallet not found"
}
```

**Validation Errors:**
```json
{
  "amount": ["Transaction amount must be positive"],
  "wallet_id": ["This field is required."]
}
```

## 9. Authentication

All endpoints require authentication. Include the authorization header:

```http
Authorization: Bearer YOUR_JWT_TOKEN
```

## 10. Pagination

All list endpoints support pagination with the following query parameters:
- `page`: Page number
- `page_size`: Number of items per page

**Response format:**
```json
{
  "count": 100,
  "next": "http://localhost:8000/api/wallet/enhanced-wallets/?page=2",
  "previous": null,
  "results": [...]
}
```

## 11. Ordering

Most endpoints support ordering with the `ordering` parameter:

```http
GET /api/wallet/enhanced-wallets/?ordering=-balance
GET /api/wallet/enhanced-wallet-transactions/?ordering=-date
```

## 12. Legacy Endpoints

For backward compatibility, the following legacy endpoints are still available:
- `/api/wallet/wallets/` - Legacy wallet management
- `/api/wallet/wallet-transactions/` - Legacy transaction management
- `/api/wallet/transactions/` - Financial transaction management
- `/api/wallet/budgets/` - Budget management
- `/api/wallet/goals/` - Financial goal management

## 13. Migration Guide

To migrate from the legacy wallet system:

1. **Create Enhanced Wallets**: Use the new enhanced wallet endpoints
2. **Migrate Transactions**: Create new transactions using the enhanced transaction system
3. **Update Frontend**: Update your frontend to use the new TypeScript interfaces
4. **Test Thoroughly**: Ensure all functionality works with the new system
5. **Deprecate Legacy**: Gradually phase out the legacy endpoints

## 14. Performance Considerations

- **Database Indexing**: Ensure proper indexes on frequently queried fields
- **Caching**: Consider caching wallet balances and statistics
- **Pagination**: Always use pagination for large datasets
- **Filtering**: Use database-level filtering for better performance

## 15. Security Features

- **User Isolation**: Users can only access their own MSE wallets
- **Transaction Validation**: All transactions are validated before processing
- **Audit Trail**: All changes are tracked with timestamps
- **Status Management**: Wallets can be suspended for security reasons

This enhanced wallet system provides a robust, scalable solution for managing financial operations across multiple MSEs while maintaining backward compatibility with existing implementations.
