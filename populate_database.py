#!/usr/bin/env python3
"""
Script to populate the Finwise database with comprehensive mockup data
"""

import os
import django
from datetime import datetime, timedelta
from decimal import Decimal
import random

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'finwise.settings')
django.setup()

from django.contrib.auth import get_user_model
from users.models import CustomUser
from mses_new.models import MSE, InputMSE, OutputMSE, ProductionMSE, MSECategory, Wallet, WalletTransaction
from markets_new.models import Market, Producer, Customer, Product, BusinessTransaction

User = get_user_model()

def create_superuser():
    """Create a superuser if it doesn't exist"""
    if not User.objects.filter(is_superuser=True).exists():
        superuser = User.objects.create_superuser(
            username='admin',
            email='admin@finwise.com',
            password='admin123',
            first_name='Admin',
            last_name='User',
            phone_number='+256700000000',
            is_verified=True
        )
        print(f"Created superuser: {superuser.username}")
        return superuser
    else:
        return User.objects.filter(is_superuser=True).first()

def create_sample_users():
    """Create sample users with different roles"""
    users = []
    
    user_data = [
        {
            'username': 'john_doe',
            'email': 'john@example.com',
            'password': 'password123',
            'first_name': 'John',
            'last_name': 'Doe',
            'phone_number': '+256700000001',
        },
        {
            'username': 'jane_smith',
            'email': 'jane@example.com',
            'password': 'password123',
            'first_name': 'Jane',
            'last_name': 'Smith',
            'phone_number': '+256700000002',
        }
    ]
    
    for data in user_data:
        user, created = User.objects.get_or_create(
            username=data['username'],
            defaults={
                'email': data['email'],
                'first_name': data['first_name'],
                'last_name': data['last_name'],
                'phone_number': data['phone_number'],
                'is_verified': True,
                'onboarding_completed': True
            }
        )
        if created:
            user.set_password(data['password'])
            user.save()
            print(f"Created user: {user.username}")
        else:
            print(f"User already exists: {user.username}")
        users.append(user)
    
    return users

def create_sample_mses(users):
    """Create sample MSEs for the users"""
    mses = []
    
    mse_data = [
        {
            'name': 'Green Valley Farm Supplies',
            'mse_type': 'micro',
            'business_type': 'Agricultural Inputs',
            'description': 'Supplier of quality farming inputs and equipment',
            'user': users[0]
        },
        {
            'name': 'Modern Textile Factory',
            'mse_type': 'small',
            'business_type': 'Textile Manufacturing',
            'description': 'Production of high-quality textiles and fabrics',
            'user': users[1]
        }
    ]
    
    for data in mse_data:
        mse, created = MSE.objects.get_or_create(
            name=data['name'],
            defaults=data
        )
        if created:
            print(f"Created MSE: {mse.name}")
        else:
            print(f"MSE already exists: {mse.name}")
        mses.append(mse)
    
    return mses

def create_mse_categories(mses):
    """Create MSE categories for the MSEs"""
    categories = []
    
    category_data = [
        {'mse': mses[0], 'primary_category': 'input', 'category_description': 'Input MSE focusing on agricultural supplies'},
        {'mse': mses[1], 'primary_category': 'production', 'category_description': 'Production MSE for textile manufacturing'},
    ]
    
    for data in category_data:
        category, created = MSECategory.objects.get_or_create(
            mse=data['mse'],
            defaults=data
        )
        if created:
            print(f"Created MSE category: {category.mse.name} - {category.get_primary_category_display()}")
        else:
            print(f"MSE category already exists: {category.mse.name}")
        categories.append(category)
    
    return categories

def create_specialized_mses(mses):
    """Create specialized MSE models (Input, Production, Output)"""
    specialized = []
    
    # Input MSE
    input_mse_data = {
        'mse': mses[0],
        'input_categories': ['Seeds', 'Fertilizers', 'Tools', 'Equipment'],
        'supplier_network_size': 25,
        'average_order_value': Decimal('150000.00'),
        'lead_time_days': 3,
        'primary_inputs': ['Organic Seeds', 'Bio Fertilizers', 'Garden Tools'],
        'seasonal_inputs': ['Rainy Season Seeds', 'Dry Season Tools']
    }
    
    input_mse, created = InputMSE.objects.get_or_create(
        mse=mses[0],
        defaults=input_mse_data
    )
    if created:
        print(f"Created Input MSE: {input_mse.mse.name}")
    specialized.append(input_mse)
    
    # Production MSE
    production_mse_data = {
        'mse': mses[1],
        'production_capacity': '1000 meters per day',
        'production_process': 'Spinning, Weaving, Dyeing, Finishing',
        'equipment_list': ['Spinning Machines', 'Power Looms', 'Dyeing Vats', 'Finishing Equipment'],
        'daily_production_target': 1000,
        'raw_materials_required': ['Cotton', 'Dyes', 'Chemicals', 'Packaging']
    }
    
    production_mse, created = ProductionMSE.objects.get_or_create(
        mse=mses[1],
        defaults=production_mse_data
    )
    if created:
        print(f"Created Production MSE: {production_mse.mse.name}")
    specialized.append(production_mse)
    
    return specialized

def create_wallets(mses):
    """Create wallets for the MSEs"""
    wallets = []
    
    for mse in mses:
        wallet_data = [
            {
                'mse': mse,
                'name': f'{mse.name} Main Wallet',
                'wallet_type': 'bank',
                'balance': Decimal('500000.00'),
                'currency': 'UGX',
                'account_number': f'ACC{mse.id}001',
                'bank_name': 'Uganda Commercial Bank'
            },
            {
                'mse': mse,
                'name': f'{mse.name} Cash Wallet',
                'wallet_type': 'cash',
                'balance': Decimal('100000.00'),
                'currency': 'UGX'
            }
        ]
        
        for data in wallet_data:
            wallet, created = Wallet.objects.get_or_create(
                mse=data['mse'],
                name=data['name'],
                defaults=data
            )
            if created:
                print(f"Created wallet: {wallet.name} for {wallet.mse.name}")
            wallets.append(wallet)
    
    return wallets

def create_markets(mses):
    """Create markets for the MSEs"""
    markets = []
    
    for mse in mses:
        market_data = [
            {
                'mse': mse,
                'name': f'{mse.name} Main Market',
                'market_type': 'output',
                'description': f'Primary market for {mse.name}',
                'location': 'Kampala, Uganda'
            }
        ]
        
        for data in market_data:
            market, created = Market.objects.get_or_create(
                mse=data['mse'],
                name=data['name'],
                defaults=data
            )
            if created:
                print(f"Created market: {market.name}")
            markets.append(market)
    
    return markets

def create_producers_and_customers(mses):
    """Create producers and customers for the MSEs"""
    producers = []
    customers = []
    
    # Sample data
    producer_names = ['Agro Supplies Ltd', 'Farm Tools Co']
    customer_names = ['Fresh Market', 'Super Foods']
    
    for mse in mses:
        # Create producers
        for i in range(2):
            producer = Producer.objects.create(
                mse=mse,
                name=f'{producer_names[i]} - {mse.name}',
                contact_person=f'Contact {i+1}',
                phone=f'+256700000{100+i}',
                email=f'producer{i+1}@{mse.name.lower().replace(" ", "")}.com',
                address=f'Address {i+1}, Kampala, Uganda',
                location='Kampala, Uganda',
                supplier_type='business',
                status='active',
                business_type='Agricultural Supplies',
                tax_id=f'TAX{i+1:03d}',
                products_supplied=f'Products for {mse.name}',
                payment_terms='Net 30',
                delivery_time='2-3 days',
                minimum_order=Decimal('50000.00'),
                rating=Decimal('4.5')
            )
            producers.append(producer)
            print(f"Created producer: {producer.name}")
        
        # Create customers
        for i in range(2):
            customer = Customer.objects.create(
                mse=mse,
                name=f'{customer_names[i]} - {mse.name}',
                contact_person=f'Customer {i+1}',
                phone=f'+256700000{200+i}',
                email=f'customer{i+1}@{mse.name.lower().replace(" ", "")}.com',
                address=f'Customer Address {i+1}, Kampala, Uganda',
                location='Kampala, Uganda',
                customer_type='business',
                status='active',
                business_type='Retail',
                tax_id=f'CUST{i+1:03d}',
                credit_limit=Decimal('500000.00'),
                payment_terms='Net 15',
                total_purchases=Decimal('0.00')
            )
            customers.append(customer)
            print(f"Created customer: {customer.name}")
    
    return producers, customers

def create_products(mses):
    """Create products for the MSEs"""
    products = []
    
    product_data = [
        {
            'mse': mses[0],  # Green Valley Farm Supplies
            'products': [
                {'name': 'Organic Seeds Pack', 'unit_price': Decimal('15000.00'), 'stock_quantity': 100},
                {'name': 'Bio Fertilizer 50kg', 'unit_price': Decimal('25000.00'), 'stock_quantity': 50},
                {'name': 'Garden Tool Set', 'unit_price': Decimal('35000.00'), 'stock_quantity': 25}
            ]
        },
        {
            'mse': mses[1],  # Modern Textile Factory
            'products': [
                {'name': 'Cotton Fabric 1m', 'unit_price': Decimal('8000.00'), 'stock_quantity': 200},
                {'name': 'Dyed Fabric 1m', 'unit_price': Decimal('12000.00'), 'stock_quantity': 150},
                {'name': 'Finished Garment', 'unit_price': Decimal('25000.00'), 'stock_quantity': 75}
            ]
        }
    ]
    
    for mse_data in product_data:
        mse = mse_data['mse']
        for product_info in mse_data['products']:
            product = Product.objects.create(
                mse=mse,
                name=product_info['name'],
                description=f'Quality {product_info["name"]} from {mse.name}',
                unit_price=product_info['unit_price'],
                stock_quantity=product_info['stock_quantity'],
                unit='piece' if 'Set' in product_info['name'] else 'kg' if 'kg' in product_info['name'] else 'piece'
            )
            products.append(product)
            print(f"Created product: {product.name} for {mse.name}")
    
    return products

def create_business_transactions(mses, wallets, producers, customers, products):
    """Create sample business transactions"""
    transactions = []
    
    transaction_types = ['purchase', 'sale', 'expense', 'income']
    statuses = ['completed', 'pending', 'cancelled']
    
    for mse in mses:
        # Create 3-5 transactions per MSE
        for i in range(random.randint(3, 5)):
            transaction_type = random.choice(transaction_types)
            amount = Decimal(random.randint(10000, 100000))
            status = random.choice(statuses)
            
            transaction = BusinessTransaction.objects.create(
                mse=mse,
                transaction_type=transaction_type,
                status=status,
                amount=amount,
                currency='UGX',
                description=f'Sample {transaction_type} transaction {i+1}',
                reference_number=f'TXN{mse.id}{i+1:03d}',
                transaction_date=datetime.now() - timedelta(days=random.randint(1, 30)),
                wallet=random.choice([w for w in wallets if w.mse == mse]),
                producer=random.choice([p for p in producers if p.mse == mse]) if transaction_type == 'purchase' else None,
                customer=random.choice([c for c in customers if c.mse == mse]) if transaction_type == 'sale' else None,
                product=random.choice([p for p in products if p.mse == mse]) if transaction_type in ['purchase', 'sale'] else None,
                quantity=random.randint(1, 10),
                unit_price=amount / random.randint(1, 10)
            )
            transactions.append(transaction)
            print(f"Created transaction: {transaction.description} for {mse.name}")
    
    return transactions

def main():
    """Main function to populate the database"""
    print("Starting database population...")
    
    # Create superuser
    admin_user = create_superuser()
    print(f"Admin user: {admin_user.username}")
    
    # Create sample users
    users = create_sample_users()
    print(f"Created {len(users)} sample users")
    
    # Create MSEs
    mses = create_sample_mses(users)
    print(f"Created {len(mses)} MSEs")
    
    # Create MSE categories
    categories = create_mse_categories(mses)
    print(f"Created {len(categories)} MSE categories")
    
    # Create specialized MSEs
    specialized = create_specialized_mses(mses)
    print(f"Created {len(specialized)} specialized MSEs")
    
    # Create wallets
    wallets = create_wallets(mses)
    print(f"Created {len(wallets)} wallets")
    
    # Create markets
    markets = create_markets(mses)
    print(f"Created {len(markets)} markets")
    
    # Create producers and customers
    producers, customers = create_producers_and_customers(mses)
    print(f"Created {len(producers)} producers and {len(customers)} customers")
    
    # Create products
    products = create_products(mses)
    print(f"Created {len(products)} products")
    
    # Create business transactions
    business_transactions = create_business_transactions(mses, wallets, producers, customers, products)
    print(f"Created {len(business_transactions)} business transactions")
    
    print("\nDatabase population completed successfully!")
    print(f"Total records created:")
    print(f"- Users: {User.objects.count()}")
    print(f"- MSEs: {MSE.objects.count()}")
    print(f"- Wallets: {Wallet.objects.count()}")
    print(f"- Products: {Product.objects.count()}")
    print(f"- Transactions: {BusinessTransaction.objects.count()}")

if __name__ == "__main__":
    main()
