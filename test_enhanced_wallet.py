#!/usr/bin/env python3
"""
Test script for the Enhanced Wallet System
"""

import os
import sys
import django
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'finwise.settings')
django.setup()

from wallet.models import EnhancedWallet, EnhancedWalletTransaction, WalletTransfer
from django.db.models import Sum

def create_test_data():
    """Create test data for the enhanced wallet system"""
    print("Creating test data for Enhanced Wallet System...")
    
    # Create test wallets
    wallet1, created = EnhancedWallet.objects.get_or_create(
        account_number='ACC001',
        defaults={
            'mse_id': 'MSE001',
            'mse_name': 'ABC Business',
            'mse_code': 'ABC',
            'account_type': 'Business',
            'currency': 'USD',
            'description': 'Main business account'
        }
    )
    
    wallet2, created = EnhancedWallet.objects.get_or_create(
        account_number='ACC002',
        defaults={
            'mse_id': 'MSE001',
            'mse_name': 'ABC Business',
            'mse_code': 'ABC',
            'account_type': 'Savings',
            'currency': 'USD',
            'description': 'Savings account'
        }
    )
    
    # Create test transactions
    if not EnhancedWalletTransaction.objects.filter(wallet=wallet1).exists():
        EnhancedWalletTransaction.objects.create(
            wallet=wallet1,
            type='Credit',
            amount=Decimal('1000.00'),
            description='Initial business capital',
            category='Payment',
            reference='INIT001',
            status='Completed'
        )
        
        EnhancedWalletTransaction.objects.create(
            wallet=wallet1,
            type='Debit',
            amount=Decimal('200.00'),
            description='Office supplies purchase',
            category='Purchase',
            reference='PUR001',
            status='Completed'
        )
    
    print("Test data creation completed!\n")

def demonstrate_functionality():
    """Demonstrate the enhanced wallet functionality"""
    print("=== Enhanced Wallet System Demonstration ===\n")
    
    wallets = EnhancedWallet.objects.all()
    print(f"Total wallets: {wallets.count()}")
    
    for wallet in wallets:
        print(f"\nWallet: {wallet.mse_name} - {wallet.account_type}")
        print(f"  Balance: {wallet.balance} {wallet.currency}")
        print(f"  Status: {wallet.status}")
        print(f"  Transaction Count: {wallet.transaction_count}")
    
    transactions = EnhancedWalletTransaction.objects.all()
    print(f"\nTotal transactions: {transactions.count()}")
    
    total_balance = wallets.aggregate(total=Sum('balance'))['total'] or 0
    print(f"\nTotal Balance: {total_balance}")

def main():
    """Main function"""
    try:
        create_test_data()
        demonstrate_functionality()
        print("\n=== Enhanced Wallet System Test Completed! ===")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
