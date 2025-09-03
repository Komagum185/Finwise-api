# Database Population Guide

This guide explains how to populate your FinWise database with sample data for testing and frontend development.

## Overview

The sample data includes:
- **MSE Categories**: Input, Producer, Output
- **Users & MSEs**: 5 sample users with different roles and locations
- **Wallets**: Each MSE gets a wallet with random initial balance
- **Products**: 12 agricultural products with realistic prices
- **Customers & Suppliers**: Sample business contacts
- **Transactions**: 50 sample transactions over the last 30 days
- **Notifications**: 30 sample notifications

## Method 1: Django Management Command (Recommended)

### Usage

```bash
# Populate with sample data (keeps existing data)
python manage.py populate_markets_data

# Clear existing data and populate fresh
python manage.py populate_markets_data --clear
```

### Features
- Comprehensive data creation
- Transaction atomicity (all-or-nothing)
- Detailed logging of created objects
- Option to clear existing data
- Professional Django management command structure

## Method 2: Standalone Script

### Usage

```bash
# Make the script executable
chmod +x populate_sample_data.py

# Run the script
python populate_sample_data.py
```

### Features
- Quick and simple execution
- Good for development and testing
- Creates smaller dataset for faster execution

## Sample Data Details

### Users & MSEs
- **john_farmer**: Producer in Kampala
- **mary_supplier**: Input supplier in Jinja
- **peter_processor**: Output processor in Mukono
- **sarah_trader**: Producer in Entebbe
- **david_merchant**: Input supplier in Masaka

### Products
- Agricultural inputs (seeds, fertilizer, pesticides)
- Fresh produce (tomatoes, beans, potatoes)
- Cash crops (coffee, tea)
- Tools and equipment

### Transactions
- Mix of purchases and sales
- Realistic quantities and amounts
- Spread over the last 30 days
- Links products, MSEs, and counterparties

## Database Schema

The sample data follows your existing models:
- **MSE**: Micro and Small Enterprise accounts
- **Wallet**: Financial accounts for each MSE
- **Product**: Items available for trade
- **Transaction**: Purchase/sale records
- **Customer/Supplier**: Business contacts
- **Notification**: System messages

## Customization

### Adding More Data
Edit the management command or script to:
- Increase quantities (e.g., more products, transactions)
- Add new product categories
- Modify price ranges
- Change geographic locations

### Modifying Data Types
- Adjust product prices and units
- Change transaction types
- Modify notification messages
- Update user roles and permissions

## Troubleshooting

### Common Issues
1. **Import Errors**: Ensure Django is properly configured
2. **Database Constraints**: Check for unique field violations
3. **Permission Issues**: Verify database access rights

### Reset Database
```bash
# Clear all data and start fresh
python manage.py populate_markets_data --clear

# Or manually reset
python manage.py flush
python manage.py migrate
```

## Frontend Integration

Once populated, your frontend can:
- Display product catalogs
- Show transaction history
- List customers and suppliers
- Display wallet balances
- Show notifications
- Generate reports and analytics

## Security Notes

- Sample data uses predictable passwords (`password123`)
- Phone numbers and NINs are fictional
- Email addresses are example.com domains
- Use different credentials in production

## Next Steps

After populating your database:
1. Test your API endpoints
2. Verify data relationships
3. Check frontend data display
4. Customize data for your specific needs
5. Add more realistic data as needed
