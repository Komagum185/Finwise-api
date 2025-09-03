#!/usr/bin/env python3
"""
Standalone script to populate the database with sample data.
Run this script from the Django project root directory.
"""

import os
import sys
import django
from decimal import Decimal
import random
from datetime import datetime, timedelta

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'finwise.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.db import transaction
from mse.models import MSECategory, MSE, Wallet
from markets.models import Customer, Supplier, Product, Transaction, Notification

User = get_user_model()


def create_sample_data():
    """Create sample data for all models"""
    
    print("Creating MSE Categories...")
    categories = create_mse_categories()
    
    print("Creating Users and MSEs...")
    users_and_mses = create_users_and_mses(categories)
    
    print("Creating Wallets...")
    wallets = create_wallets(users_and_mses)
    
    print("Creating Products...")
    products = create_products(users_and_mses)
    
    print("Creating Customers and Suppliers...")
    customers = create_customers(users_and_mses)
    suppliers = create_suppliers(users_and_mses)
    
    print("Creating Transactions...")
    transactions = create_transactions(users_and_mses, products, customers, suppliers)
    
    print("Creating Notifications...")
    notifications = create_notifications(users_and_mses)
    
    print("Sample data creation completed successfully!")


def create_mse_categories():
    """Create MSE categories"""
    categories = []
    category_data = [
        {'name': 'input', 'description': 'Agricultural inputs and supplies'},
        {'name': 'producer', 'description': 'Agricultural producers and farmers'},
        {'name': 'output', 'description': 'Agricultural output and processing'},
    ]
    
    for data in category_data:
        category, created = MSECategory.objects.get_or_create(
            name=data['name'],
            defaults={'description': data['description']}
        )
        categories.append(category)
        if created:
            print(f'Created MSE category: {category.name}')
    
    return categories


def create_users_and_mses(categories):
    """Create sample users and MSEs"""
    users_and_mses = []
    
    # Sample data for users and MSEs
    sample_data = [
        {
            'username': 'john_farmer',
            'first_name': 'John',
            'last_name': 'Farmer',
            'phone_number': '+256701234567',
            'NIN': 'CM123456789ABCDEF',
            'role': 'mse',
            'email': 'john.farmer@example.com',
            'category': categories[1],  # producer
            'location': 'Kampala, Uganda',
            'status': 'approved'
        },
        {
            'username': 'mary_supplier',
            'first_name': 'Mary',
            'last_name': 'Supplier',
            'phone_number': '+256702345678',
            'NIN': 'CM234567890BCDEFG',
            'role': 'mse',
            'email': 'mary.supplier@example.com',
            'category': categories[0],  # input
            'location': 'Jinja, Uganda',
            'status': 'approved'
        },
        {
            'username': 'peter_processor',
            'first_name': 'Peter',
            'last_name': 'Processor',
            'phone_number': '+256703456789',
            'NIN': 'CM345678901CDEFGH',
            'role': 'mse',
            'email': 'peter.processor@example.com',
            'category': categories[2],  # output
            'location': 'Mukono, Uganda',
            'status': 'approved'
        }
    ]
    
    for data in sample_data:
        # Create user
        user = User.objects.create_user(
            username=data['username'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            phone_number=data['phone_number'],
            NIN=data['NIN'],
            role=data['role'],
            email=data['email'],
            password='password123',
            is_approved=True
        )
        
        # Create MSE
        mse = MSE.objects.create(
            owner=user,
            first_name=data['first_name'],
            last_name=data['last_name'],
            nin=data['NIN'],
            phone=data['phone_number'],
            email=data['email'],
            category=data['category'],
            location=data['location'],
            status=data['status']
        )
        
        users_and_mses.append((user, mse))
        print(f'Created user and MSE: {user.username}')
    
    return users_and_mses


def create_wallets(users_and_mses):
    """Create wallets for MSEs"""
    wallets = []
    
    for user, mse in users_and_mses:
        # Random initial balance between 100,000 and 2,000,000 UGX
        initial_balance = Decimal(random.randint(100000, 2000000))
        
        wallet = Wallet.objects.create(
            mse=mse,
            balance=initial_balance,
            currency='UGX'
        )
        
        wallets.append(wallet)
        print(f'Created wallet for {mse.first_name} with balance: {wallet.balance} {wallet.currency}')
    
    return wallets


def create_products(users_and_mses):
    """Create sample products"""
    products = []
    
    # Sample product data
    product_data = [
        {'name': 'Maize Seeds', 'price': Decimal('15000.00'), 'unit': 'kg'},
        {'name': 'Fertilizer NPK', 'price': Decimal('45000.00'), 'unit': '50kg bag'},
        {'name': 'Fresh Tomatoes', 'price': Decimal('3000.00'), 'unit': 'kg'},
        {'name': 'Coffee Beans', 'price': Decimal('8000.00'), 'unit': 'kg'},
        {'name': 'Bananas', 'price': Decimal('2500.00'), 'unit': 'bunch'},
    ]
    
    for data in product_data:
        # Randomly assign product to an MSE
        user, mse = random.choice(users_and_mses)
        
        product = Product.objects.create(
            mse=mse,
            name=data['name'],
            price=data['price'],
            unit=data['unit']
        )
        
        products.append(product)
        print(f'Created product: {product.name} at {product.price} UGX per {product.unit}')
    
    return products


def create_customers(users_and_mses):
    """Create sample customers"""
    customers = []
    
    # Sample customer data
    customer_data = [
        {'name': 'Alice Johnson', 'phone_number': '+256711111111'},
        {'name': 'Bob Smith', 'phone_number': '+256722222222'},
        {'name': 'Carol Davis', 'phone_number': '+256733333333'},
    ]
    
    for data in customer_data:
        # Randomly assign customer to an MSE
        user, mse = random.choice(users_and_mses)
        
        customer = Customer.objects.create(
            mse=mse,
            name=data['name'],
            phone_number=data['phone_number']
        )
        
        customers.append(customer)
        print(f'Created customer: {customer.name} for {mse.first_name}')
    
    return customers


def create_suppliers(users_and_mses):
    """Create sample suppliers"""
    suppliers = []
    
    # Sample supplier data
    supplier_data = [
        {'name': 'Agro Supply Co.', 'phone_number': '+256791111111'},
        {'name': 'Farm Tools Ltd.', 'phone_number': '+256792222222'},
        {'name': 'Seed Bank Uganda', 'phone_number': '+256793333333'},
    ]
    
    for data in supplier_data:
        # Randomly assign supplier to an MSE
        user, mse = random.choice(users_and_mses)
        
        supplier = Supplier.objects.create(
            mse=mse,
            name=data['name'],
            phone_number=data['phone_number']
        )
        
        suppliers.append(supplier)
        print(f'Created supplier: {supplier.name} for {mse.first_name}')
    
    return suppliers


def create_transactions(users_and_mses, products, customers, suppliers):
    """Create sample transactions"""
    transactions = []
    
    # Generate transactions for the last 30 days
    end_date = datetime.now()
    
    for _ in range(20):  # Create 20 sample transactions
        # Random transaction type
        transaction_type = random.choice(['purchase', 'sale'])
        
        # Random MSE
        user, mse = random.choice(users_and_mses)
        
        # Random product
        product = random.choice(products)
        
        # Random counterparty
        if transaction_type == 'purchase':
            counterparty = random.choice(suppliers)
            counterparty_name = counterparty.name
        else:
            counterparty = random.choice(customers)
            counterparty_name = counterparty.name
        
        # Random quantity and amount
        quantity = Decimal(random.randint(1, 100))
        amount = product.price * quantity
        
        # Random date within last 30 days
        random_days = random.randint(0, 30)
        random_date = end_date - timedelta(days=random_days)
        
        transaction = Transaction.objects.create(
            mse=mse,
            type=transaction_type,
            product=product,
            counterparty_name=counterparty_name,
            amount=amount,
            quantity=quantity,
            created_at=random_date
        )
        
        transactions.append(transaction)
    
    print(f'Created {len(transactions)} transactions')
    return transactions


def create_notifications(users_and_mses):
    """Create sample notifications"""
    notifications = []
    
    # Sample notification messages
    notification_messages = [
        'New product available: Fresh tomatoes at great prices!',
        'Your order has been confirmed and is being processed.',
        'Payment received for your recent sale.',
        'New customer inquiry about your products.',
        'Your account has been successfully verified.',
    ]
    
    for _ in range(15):  # Create 15 sample notifications
        # Random MSE
        user, mse = random.choice(users_and_mses)
        
        # Random message
        message = random.choice(notification_messages)
        
        # Random read status
        is_read = random.choice([True, False])
        
        # Random date within last 7 days
        random_days = random.randint(0, 7)
        random_date = datetime.now() - timedelta(days=random_days)
        
        notification = Notification.objects.create(
            mse=mse,
            message=message,
            is_read=is_read,
            created_at=random_date
        )
        
        notifications.append(notification)
    
    print(f'Created {len(notifications)} notifications')
    return notifications


if __name__ == '__main__':
    try:
        with transaction.atomic():
            create_sample_data()
        print("Database populated successfully!")
    except Exception as e:
        print(f"Error populating database: {str(e)}")
        sys.exit(1)
