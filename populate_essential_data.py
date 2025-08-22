#!/usr/bin/env python
"""
Essential Data Population Script for Finwise API
This script populates the database with essential sample data for testing.
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
from mses.models import MSE, Wallet, WalletTransaction
from payments.models import PaymentProvider, PaymentTransaction
from marketplace.models import Product, MarketOpportunity, ProductReview

User = get_user_model()

def create_test_users():
    """Create essential test users"""
    print("Creating test users...")
    
    users_data = [
        {
            'username': 'admin',
            'email': 'admin@finwise.com',
            'password': 'admin123',
            'first_name': 'Admin',
            'last_name': 'User',
            'role': 'Admin',
            'business_type': 'Financial Services',
            'business_location': 'Kampala, Uganda',
            'business_description': 'System administrator',
            'phone_number': '+256700000001',
            'is_staff': True,
            'is_superuser': True
        },
        {
            'username': 'farmer1',
            'email': 'farmer1@finwise.com',
            'password': 'password123',
            'first_name': 'John',
            'last_name': 'Farmer',
            'role': 'MicroBusiness',
            'business_type': 'Small Scale Farming',
            'business_location': 'Masaka, Uganda',
            'business_description': 'Small-scale organic farming',
            'phone_number': '+256700000002'
        },
        {
            'username': 'supplier1',
            'email': 'supplier1@finwise.com',
            'password': 'password123',
            'first_name': 'Sarah',
            'last_name': 'Supplier',
            'role': 'Input MSE',
            'business_type': 'Seed Supplier, Fertilizer Supplier',
            'business_location': 'Jinja, Uganda',
            'business_description': 'Agricultural input supplier',
            'phone_number': '+256700000003'
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
        else:
            print(f"User already exists: {user.username}")
        created_users.append(user)
    
    return created_users

def create_payment_providers():
    """Create essential payment providers"""
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
        else:
            print(f"Payment provider already exists: {provider.name}")
        created_providers.append(provider)
    
    return created_providers

def create_sample_products(users):
    """Create sample marketplace products"""
    print("Creating sample products...")
    
    # Clear existing products first
    Product.objects.all().delete()
    
    products_data = [
        {
            'seller': users[2],  # Supplier
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
            'certifications': ['Organic Certified'],
            'specifications': {'germination_rate': '95%'}
        },
        {
            'seller': users[2],  # Supplier
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
            'specifications': {'npk_ratio': '20-20-20'}
        }
    ]
    
    created_products = []
    for product_data in products_data:
        product = Product.objects.create(**product_data)
        print(f"Created product: {product.name}")
        created_products.append(product)
    
    return created_products

def create_sample_opportunities(users):
    """Create sample market opportunities"""
    print("Creating sample opportunities...")
    
    # Clear existing opportunities first
    MarketOpportunity.objects.all().delete()
    
    opportunities_data = [
        {
            'creator': users[1],  # Farmer
            'title': 'Bulk Maize Seeds Supply Request',
            'description': 'Looking for reliable supplier of 500kg high-quality maize seeds',
            'opportunity_type': 'bulk_purchase',
            'required_products': ['High-Yield Maize Seeds'],
            'quantity_needed': '500 kg',
            'budget_range': 'UGX 2,000,000 - 2,500,000',
            'deadline': timezone.now() + timedelta(days=30),
            'location': 'Masaka, Uganda',
            'contact_person': 'John Farmer',
            'contact_phone': '+256700000002',
            'contact_email': 'farmer1@finwise.com',
            'requirements': 'Must be organic certified, 95% germination rate minimum'
        }
    ]
    
    created_opportunities = []
    for opportunity_data in opportunities_data:
        opportunity = MarketOpportunity.objects.create(**opportunity_data)
        print(f"Created opportunity: {opportunity.title}")
        created_opportunities.append(opportunity)
    
    return created_opportunities

def create_sample_payment_transactions(users, providers):
    """Create sample payment transactions"""
    print("Creating sample payment transactions...")
    
    # Clear existing transactions first
    PaymentTransaction.objects.all().delete()
    
    for user in users[1:]:  # Skip admin user
        for i in range(3):  # 3 transactions per user
            provider = random.choice(providers)
            amount = Decimal(str(random.randint(10000, 100000)))
            fees = provider.calculate_fees(amount)
            
            transaction = PaymentTransaction.objects.create(
                user=user,
                type=random.choice(['qr_payment', 'mobile_money']),
                amount=amount,
                currency='UGX',
                fees=fees,
                net_amount=amount - fees,
                provider=provider,
                reference=f'PAY{uuid.uuid4().hex[:8].upper()}',
                status='completed',
                description=f'Sample payment transaction {i+1}',
                created_at=timezone.now() - timedelta(days=random.randint(1, 30))
            )
            print(f"Created payment transaction: {transaction.reference} - {transaction.amount}")

def create_sample_reviews(users, products):
    """Create sample product reviews"""
    print("Creating sample reviews...")
    
    for product in products:
        for i in range(2):  # 2 reviews per product
            reviewer = random.choice(users[1:])  # Skip admin user
            review, created = ProductReview.objects.get_or_create(
                product=product,
                reviewer=reviewer,
                defaults={
                    'rating': random.randint(4, 5),
                    'comment': f'Great quality product! Highly recommended.',
                    'created_at': timezone.now() - timedelta(days=random.randint(1, 30))
                }
            )
            if created:
                print(f"Created review: {review.rating} stars for {product.name}")
            else:
                print(f"Review already exists for {product.name} by {reviewer.username}")

def main():
    """Main function to populate essential sample data"""
    print("Starting essential data population...")
    
    # Create users
    users = create_test_users()
    
    # Create payment providers
    providers = create_payment_providers()
    
    # Create sample products
    products = create_sample_products(users)
    
    # Create sample opportunities
    opportunities = create_sample_opportunities(users)
    
    # Create sample payment transactions
    create_sample_payment_transactions(users, providers)
    
    # Create sample reviews
    create_sample_reviews(users, products)
    
    print("\n" + "="*50)
    print("Essential data population completed successfully!")
    print("="*50)
    print(f"Created {len(users)} users")
    print(f"Created {len(providers)} payment providers")
    print(f"Created {len(products)} products")
    print(f"Created {len(opportunities)} opportunities")
    print("\nYou can now test the frontend with this sample data!")
    print("Default login credentials:")
    print("Username: admin, Password: admin123")
    print("Username: farmer1, Password: password123")
    print("Username: supplier1, Password: password123")

if __name__ == '__main__':
    main()
