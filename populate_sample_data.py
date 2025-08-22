#!/usr/bin/env python
"""
Sample Data Population Script for Finwise API
This script populates the database with realistic sample data for testing and demonstration.
"""

import os
import sys
import django
from datetime import datetime, timedelta
from decimal import Decimal
import random
import uuid

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'finwise.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone
from users.models import CustomUser
from mses.models import MSE, InputMSE, OutputMSE, ProductionMSE, MSECategory, Wallet, WalletTransaction
from loans.models import LoanApplication, Loan, LoanSchedule, LoanPayment
from kyc.models import KYCDocument, BankAccount, MobileMoneyAccount, KYCVerification
from customers.models import Customer, CustomerFeedback, SMSCampaign
from wallet.models import BusinessHealth, PaymentTransaction, BulkPayment, BulkPaymentRecipient
from reports.models import SalesData, ProductPerformance, MarketTrends, Predictions
from payments.models import PaymentProvider, QRPayment, ScheduledTransfer, PaymentTransaction as PaymentTransactionModel
from marketplace.models import Product, MarketOpportunity, OpportunityApplication, MarketplaceMessage, ProductReview, MarketplaceNotification

User = get_user_model()

def create_sample_users():
    """Create sample users with different roles"""
    print("Creating sample users...")
    
    users_data = [
        {
            'username': 'admin_user',
            'email': 'admin@finwise.com',
            'password': 'admin123',
            'first_name': 'Admin',
            'last_name': 'User',
            'role': 'Admin',
            'business_type': 'Financial Services',
            'business_location': 'Kampala, Uganda',
            'business_description': 'System administrator for Finwise platform',
            'phone_number': '+256700000001',
            'is_staff': True,
            'is_superuser': True
        },
        {
            'username': 'input_mse1',
            'email': 'seed_supplier@finwise.com',
            'password': 'password123',
            'first_name': 'John',
            'last_name': 'SeedSupplier',
            'role': 'Input MSE',
            'business_type': 'Seed Supplier, Fertilizer Supplier',
            'business_location': 'Jinja, Uganda',
            'business_description': 'Leading supplier of high-quality seeds and fertilizers',
            'phone_number': '+256700000002'
        },
        {
            'username': 'production_mse1',
            'email': 'grain_miller@finwise.com',
            'password': 'password123',
            'first_name': 'Sarah',
            'last_name': 'GrainMiller',
            'role': 'Production MSE',
            'business_type': 'Grain Milling, Oil Processing',
            'business_location': 'Mukono, Uganda',
            'business_description': 'Professional grain milling and oil processing services',
            'phone_number': '+256700000003'
        },
        {
            'username': 'output_mse1',
            'email': 'agro_retailer@finwise.com',
            'password': 'password123',
            'first_name': 'David',
            'last_name': 'AgroRetailer',
            'role': 'Output MSE',
            'business_type': 'Agricultural Retail Store, Wholesale Distribution',
            'business_location': 'Kampala, Uganda',
            'business_description': 'Comprehensive agricultural retail and wholesale services',
            'phone_number': '+256700000004'
        },
        {
            'username': 'micro_business1',
            'email': 'small_farmer@finwise.com',
            'password': 'password123',
            'first_name': 'Mary',
            'last_name': 'SmallFarmer',
            'role': 'MicroBusiness',
            'business_type': 'Small Scale Farming',
            'business_location': 'Masaka, Uganda',
            'business_description': 'Small-scale organic farming with focus on vegetables',
            'phone_number': '+256700000005'
        }
    ]
    
    created_users = []
    for user_data in users_data:
        user, created = User.objects.get_or_create(
            username=user_data['username'],
            defaults=user_data
        )
        if created:
            user.set_password(user_data['password'])
            user.save()
            print(f"Created user: {user.username}")
        created_users.append(user)
    
    return created_users

def create_payment_providers():
    """Create sample payment providers"""
    print("Creating payment providers...")
    
    providers_data = [
        {
            'name': 'MTN Mobile Money',
            'provider_id': 'mtn_uganda',
            'type': 'mobile_money',
            'country': 'UG',
            'currency': 'UGX',
            'fee_percentage': Decimal('0.5'),
            'fee_fixed': Decimal('100'),
            'min_amount': Decimal('1000'),
            'max_amount': Decimal('1000000'),
            'status': 'active'
        },
        {
            'name': 'Airtel Money',
            'provider_id': 'airtel_uganda',
            'type': 'mobile_money',
            'country': 'UG',
            'currency': 'UGX',
            'fee_percentage': Decimal('0.5'),
            'fee_fixed': Decimal('100'),
            'min_amount': Decimal('1000'),
            'max_amount': Decimal('1000000'),
            'status': 'active'
        },
        {
            'name': 'M-Pesa',
            'provider_id': 'mpesa_kenya',
            'type': 'mobile_money',
            'country': 'KE',
            'currency': 'KES',
            'fee_percentage': Decimal('0.5'),
            'fee_fixed': Decimal('50'),
            'min_amount': Decimal('100'),
            'max_amount': Decimal('70000'),
            'status': 'active'
        },
        {
            'name': 'Bank Transfer',
            'provider_id': 'bank_transfer',
            'type': 'bank',
            'country': 'UG',
            'currency': 'UGX',
            'fee_percentage': Decimal('0.1'),
            'fee_fixed': Decimal('500'),
            'min_amount': Decimal('10000'),
            'max_amount': Decimal('10000000'),
            'status': 'active'
        }
    ]
    
    created_providers = []
    for provider_data in providers_data:
        provider, created = PaymentProvider.objects.get_or_create(
            provider_id=provider_data['provider_id'],
            defaults=provider_data
        )
        if created:
            print(f"Created payment provider: {provider.name}")
        created_providers.append(provider)
    
    return created_providers

def create_marketplace_products(users, providers):
    """Create sample marketplace products"""
    print("Creating marketplace products...")
    
    products_data = [
        {
            'seller': users[1],  # Input MSE
            'name': 'High-Yield Maize Seeds',
            'category': 'seeds',
            'subcategory': 'Maize',
            'description': 'Premium quality maize seeds with 95% germination rate',
            'price': Decimal('5000'),
            'stock': 100,
            'unit': 'kg',
            'quality_grade': 'A',
            'is_organic': True,
            'origin': 'Uganda',
            'certifications': ['Organic Certified', 'ISO 9001'],
            'specifications': {'germination_rate': '95%', 'purity': '99%'}
        },
        {
            'seller': users[1],  # Input MSE
            'name': 'NPK Fertilizer',
            'category': 'fertilizers',
            'subcategory': 'NPK',
            'description': 'Balanced NPK fertilizer for all crops',
            'price': Decimal('3500'),
            'stock': 200,
            'unit': 'kg',
            'quality_grade': 'A',
            'is_organic': False,
            'origin': 'Kenya',
            'certifications': ['ISO 9001'],
            'specifications': {'npk_ratio': '20-20-20', 'nitrogen': '20%'}
        },
        {
            'seller': users[2],  # Production MSE
            'name': 'Groundnut Oil',
            'category': 'processed_goods',
            'subcategory': 'Cooking Oil',
            'description': 'Pure groundnut oil extracted from local groundnuts',
            'price': Decimal('8000'),
            'stock': 50,
            'unit': 'liters',
            'quality_grade': 'A',
            'is_organic': True,
            'origin': 'Uganda',
            'processing_method': 'Cold Pressed',
            'certifications': ['Organic Certified'],
            'specifications': {'extraction_method': 'Cold Pressed', 'shelf_life': '12 months'}
        },
        {
            'seller': users[2],  # Production MSE
            'name': 'Maize Flour',
            'category': 'processed_goods',
            'subcategory': 'Flour',
            'description': 'Fine maize flour for ugali and porridge',
            'price': Decimal('3000'),
            'stock': 150,
            'unit': 'kg',
            'quality_grade': 'B',
            'is_organic': False,
            'origin': 'Uganda',
            'processing_method': 'Stone Ground',
            'certifications': ['ISO 9001'],
            'specifications': {'grinding_method': 'Stone Ground', 'protein_content': '8%'}
        },
        {
            'seller': users[3],  # Output MSE
            'name': 'Garden Tools Set',
            'category': 'tools',
            'subcategory': 'Hand Tools',
            'description': 'Complete set of essential garden tools',
            'price': Decimal('25000'),
            'stock': 30,
            'unit': 'sets',
            'quality_grade': 'A',
            'is_organic': False,
            'origin': 'China',
            'certifications': ['ISO 9001'],
            'specifications': {'material': 'Stainless Steel', 'warranty': '2 years'}
        }
    ]
    
    created_products = []
    for product_data in products_data:
        product, created = Product.objects.get_or_create(
            seller=product_data['seller'],
            name=product_data['name'],
            defaults=product_data
        )
        if created:
            print(f"Created product: {product.name}")
        else:
            print(f"Product already exists: {product.name}")
        created_products.append(product)
    
    return created_products

def create_market_opportunities(users):
    """Create sample market opportunities"""
    print("Creating market opportunities...")
    
    opportunities_data = [
        {
            'creator': users[3],  # Output MSE
            'title': 'Bulk Maize Seeds Supply Tender',
            'description': 'Looking for reliable supplier of 1000kg high-quality maize seeds',
            'opportunity_type': 'tender',
            'required_products': ['High-Yield Maize Seeds'],
            'quantity_needed': '1000 kg',
            'budget_range': 'UGX 4,000,000 - 5,000,000',
            'deadline': timezone.now() + timedelta(days=30),
            'location': 'Kampala, Uganda',
            'contact_person': 'David AgroRetailer',
            'contact_phone': '+256700000004',
            'contact_email': 'agro_retailer@finwise.com',
            'requirements': 'Must be organic certified, 95% germination rate minimum'
        },
        {
            'creator': users[2],  # Production MSE
            'title': 'Organic Groundnut Supply Partnership',
            'description': 'Seeking long-term partnership for organic groundnut supply',
            'opportunity_type': 'partnership',
            'required_products': ['Organic Groundnuts'],
            'quantity_needed': '500 kg monthly',
            'budget_range': 'UGX 3,000,000 - 4,000,000 per month',
            'deadline': timezone.now() + timedelta(days=60),
            'location': 'Mukono, Uganda',
            'contact_person': 'Sarah GrainMiller',
            'contact_phone': '+256700000003',
            'contact_email': 'grain_miller@finwise.com',
            'requirements': 'Must be organic certified, consistent quality, reliable delivery'
        }
    ]
    
    created_opportunities = []
    for opportunity_data in opportunities_data:
        opportunity, created = MarketOpportunity.objects.get_or_create(
            creator=opportunity_data['creator'],
            title=opportunity_data['title'],
            defaults=opportunity_data
        )
        if created:
            print(f"Created opportunity: {opportunity.title}")
        else:
            print(f"Opportunity already exists: {opportunity.title}")
        created_opportunities.append(opportunity)
    
    return created_opportunities

def create_loan_applications(users):
    """Create sample loan applications"""
    print("Creating loan applications...")
    
    # First, let's create MSE objects for the users
    mses = []
    for user in users[1:]:  # Skip admin user
        mse, created = MSE.objects.get_or_create(
            user=user,
            defaults={
                'name': f"{user.first_name} {user.last_name} Business",
                'mse_type': 'small',
                'status': 'active',
                'phone': user.phone_number,
                'email': user.email,
                'business_type': user.business_type,
                'description': user.business_description,
                'address': user.business_location
            }
        )
        if created:
            print(f"Created MSE for {user.username}")
        mses.append(mse)
    
    loan_data = [
        {
            'applicant': users[1],  # Input MSE
            'mse': mses[0],
            'requested_amount': Decimal('5000000'),
            'purpose': 'Expand seed storage facility and purchase new equipment',
            'business_plan': 'Detailed plan for expanding storage capacity by 50%',
            'collateral_description': 'Storage facility and equipment',
            'status': 'approved'
        },
        {
            'applicant': users[4],  # Micro Business
            'mse': mses[3],
            'requested_amount': Decimal('1000000'),
            'purpose': 'Purchase organic farming supplies and expand vegetable production',
            'business_plan': 'Plan to increase vegetable production by 40%',
            'collateral_description': 'Farming equipment and land lease',
            'status': 'submitted'
        }
    ]
    
    created_loans = []
    for loan_info in loan_data:
        loan_application = LoanApplication.objects.create(**loan_info)
        print(f"Created loan application: {loan_application.requested_amount} - {loan_application.status}")
        created_loans.append(loan_application)
    
    return created_loans

def create_customers(users):
    """Create sample customers"""
    print("Creating customers...")
    
    customers_data = [
        {
            'user': users[1],  # Input MSE
            'name': 'Kampala Farmers Cooperative',
            'phone': '+256700000101',
            'email': 'info@kampalafarmers.co.ug',
            'location': 'Kampala, Uganda',
            'customer_type': 'wholesale',
            'total_purchases': 15,
            'total_spent': Decimal('25000000'),
            'average_order_value': Decimal('1666667'),
            'loyalty_points': 2500,
            'rating': Decimal('4.5'),
            'notes': 'Reliable wholesale customer, pays on time'
        },
        {
            'user': users[2],  # Production MSE
            'name': 'Jinja Supermarket Chain',
            'phone': '+256700000102',
            'email': 'procurement@jinjasupermarket.com',
            'location': 'Jinja, Uganda',
            'customer_type': 'retail',
            'total_purchases': 8,
            'total_spent': Decimal('12000000'),
            'average_order_value': Decimal('1500000'),
            'loyalty_points': 1200,
            'rating': Decimal('4.2'),
            'notes': 'Regular customer, prefers organic products'
        },
        {
            'user': users[4],  # Micro Business
            'name': 'Local Market Vendors',
            'phone': '+256700000103',
            'email': 'vendors@localmarket.ug',
            'location': 'Masaka, Uganda',
            'customer_type': 'regular',
            'total_purchases': 25,
            'total_spent': Decimal('8000000'),
            'average_order_value': Decimal('320000'),
            'loyalty_points': 800,
            'rating': Decimal('4.8'),
            'notes': 'Small but frequent purchases, very loyal'
        }
    ]
    
    created_customers = []
    for customer_data in customers_data:
        customer, created = Customer.objects.get_or_create(
            user=customer_data['user'],
            phone=customer_data['phone'],
            defaults=customer_data
        )
        if created:
            print(f"Created customer: {customer.name}")
        else:
            print(f"Customer already exists: {customer.name}")
        created_customers.append(customer)
    
    return created_customers

def create_wallet_transactions(users):
    """Create sample wallet transactions"""
    print("Creating wallet transactions...")
    
    # Create wallets for users
    wallets = []
    for user in users[1:]:  # Skip admin user
        # Get or create MSE for the user
        mse, created = MSE.objects.get_or_create(
            user=user,
            defaults={
                'name': f"{user.first_name} {user.last_name} Business",
                'mse_type': 'small',
                'status': 'active',
                'phone': user.phone_number,
                'email': user.email,
                'business_type': user.business_type,
                'description': user.business_description,
                'address': user.business_location
            }
        )
        
        wallet, created = Wallet.objects.get_or_create(
            mse=mse,
            defaults={
                'account_number': f'WAL{str(user.id)[:8].upper()}',
                'account_type': 'Business',
                'balance': Decimal('1000000'),
                'currency': 'UGX',
                'status': 'Active',
                'description': f'Business wallet for {user.username}'
            }
        )
        if created:
            print(f"Created wallet for {user.username}")
        wallets.append(wallet)
    
    # Create sample transactions
    transaction_types = ['Credit', 'Debit', 'Transfer']
    descriptions = [
        'Product sale payment',
        'Supplier payment',
        'Loan disbursement',
        'Customer refund',
        'Service fee',
        'Mobile money transfer'
    ]
    
    for wallet in wallets:
        for i in range(10):  # 10 transactions per wallet
            transaction = WalletTransaction.objects.create(
                wallet=wallet,
                type=random.choice(transaction_types),
                amount=Decimal(str(random.randint(50000, 500000))),
                description=random.choice(descriptions),
                date=timezone.now() - timedelta(days=random.randint(1, 30)),
                status='Completed'
            )
            print(f"Created transaction: {transaction.type} - {transaction.amount}")
    
    return wallets

def create_payment_transactions(users, providers):
    """Create sample payment transactions"""
    print("Creating payment transactions...")
    
    for user in users[1:]:  # Skip admin user
        for i in range(5):  # 5 payment transactions per user
            provider = random.choice(providers)
            amount = Decimal(str(random.randint(10000, 100000)))
            fees = provider.calculate_fees(amount)
            
            transaction = PaymentTransactionModel.objects.create(
                user=user,
                type=random.choice(['qr_payment', 'mobile_money', 'bank_transfer']),
                amount=amount,
                currency='UGX',
                fees=fees,
                net_amount=amount - fees,
                provider=provider,
                reference=f'PAY{uuid.uuid4().hex[:8].upper()}',
                status=random.choice(['completed', 'pending', 'failed']),
                description=f'Sample payment transaction {i+1}',
                created_at=timezone.now() - timedelta(days=random.randint(1, 30))
            )
            print(f"Created payment transaction: {transaction.reference} - {transaction.amount}")

def create_product_reviews(users, products):
    """Create sample product reviews"""
    print("Creating product reviews...")
    
    for product in products:
        # Create 2-4 reviews per product
        for i in range(random.randint(2, 4)):
            reviewer = random.choice(users[1:])  # Skip admin user
            review = ProductReview.objects.create(
                product=product,
                reviewer=reviewer,
                rating=random.randint(3, 5),
                comment=f'Sample review {i+1} for {product.name}. Great quality and service!',
                created_at=timezone.now() - timedelta(days=random.randint(1, 60))
            )
            print(f"Created review: {review.rating} stars for {product.name}")

def create_marketplace_messages(users, products, opportunities):
    """Create sample marketplace messages"""
    print("Creating marketplace messages...")
    
    message_types = ['product_inquiry', 'opportunity_inquiry', 'general']
    subjects = [
        'Product availability inquiry',
        'Bulk order request',
        'Partnership opportunity',
        'Price negotiation',
        'Delivery schedule discussion'
    ]
    
    for i in range(10):  # Create 10 sample messages
        sender = random.choice(users[1:])
        recipient = random.choice([u for u in users[1:] if u != sender])
        
        message = MarketplaceMessage.objects.create(
            sender=sender,
            recipient=recipient,
            subject=random.choice(subjects),
            message=f'Sample message {i+1} from {sender.username} to {recipient.username}',
            message_type=random.choice(message_types),
            product=random.choice(products) if random.choice([True, False]) else None,
            opportunity=random.choice(opportunities) if random.choice([True, False]) else None,
            created_at=timezone.now() - timedelta(days=random.randint(1, 30))
        )
        print(f"Created message: {message.subject}")

def create_sales_data(users):
    """Create sample sales data"""
    print("Creating sales data...")
    
    for user in users[1:]:  # Skip admin user
        for i in range(30):  # 30 days of sales data
            date = timezone.now().date() - timedelta(days=i)
            sales_data = SalesData.objects.create(
                user=user,
                date=date,
                revenue=Decimal(str(random.randint(100000, 1000000))),
                orders=random.randint(5, 50),
                customers=random.randint(2, 20),
                average_order_value=Decimal(str(random.randint(20000, 100000)))
            )
            print(f"Created sales data for {user.username} on {date}")

def create_business_health_data(users):
    """Create sample business health data"""
    print("Creating business health data...")
    
    for user in users[1:]:  # Skip admin user
        health_data = BusinessHealth.objects.create(
            user=user,
            financial_health=Decimal(str(random.randint(70, 95))),
            inventory_efficiency=Decimal(str(random.randint(75, 90))),
            customer_satisfaction=Decimal(str(random.randint(80, 95))),
            overall_score=Decimal(str(random.randint(75, 90))),
            recommendations=[
                'Consider expanding product range',
                'Improve customer service response time',
                'Optimize inventory management',
                'Explore new market opportunities'
            ],
            calculated_at=timezone.now()
        )
        print(f"Created business health data for {user.username}")

def main():
    """Main function to populate all sample data"""
    print("Starting sample data population...")
    
    # Create users
    users = create_sample_users()
    
    # Create payment providers
    providers = create_payment_providers()
    
    # Create marketplace products
    products = create_marketplace_products(users, providers)
    
    # Create market opportunities
    opportunities = create_market_opportunities(users)
    
    # Create loan applications
    loans = create_loan_applications(users)
    
    # Create customers
    customers = create_customers(users)
    
    # Create wallet transactions
    wallets = create_wallet_transactions(users)
    
    # Create payment transactions
    create_payment_transactions(users, providers)
    
    # Create product reviews
    create_product_reviews(users, products)
    
    # Create marketplace messages
    create_marketplace_messages(users, products, opportunities)
    
    # Create sales data
    create_sales_data(users)
    
    # Create business health data
    create_business_health_data(users)
    
    print("\n" + "="*50)
    print("Sample data population completed successfully!")
    print("="*50)
    print(f"Created {len(users)} users")
    print(f"Created {len(providers)} payment providers")
    print(f"Created {len(products)} marketplace products")
    print(f"Created {len(opportunities)} market opportunities")
    print(f"Created {len(loans)} loan applications")
    print(f"Created {len(customers)} customers")
    print(f"Created {len(wallets)} wallets")
    print("\nYou can now test the frontend with this sample data!")
    print("Default login credentials:")
    print("Username: admin_user, Password: admin123")
    print("Username: input_mse1, Password: password123")
    print("Username: production_mse1, Password: password123")
    print("Username: output_mse1, Password: password123")
    print("Username: micro_business1, Password: password123")

if __name__ == '__main__':
    main()
