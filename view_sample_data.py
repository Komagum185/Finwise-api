#!/usr/bin/env python3
"""
Script to view the sample data in your database.
Run this after populating the database to see what data is available.
"""

import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'finwise.settings')
django.setup()

from django.contrib.auth import get_user_model
from mse.models import MSECategory, MSE, Wallet
from markets.models import Customer, Supplier, Product, Transaction, Notification
from groups.models import Group, GroupMembership, GroupWallet
from loans.models import LoanProduct, GroupLoan, GroupLoanRepayment

User = get_user_model()


def view_sample_data():
    """Display sample data from the database"""
    
    print("=" * 60)
    print("FINWISE DATABASE SAMPLE DATA OVERVIEW")
    print("=" * 60)
    
    # Users and MSEs
    print("\n📊 USERS & MSEs:")
    print("-" * 30)
    users = User.objects.filter(role='mse')
    for user in users:
        try:
            mse = user.mse_accounts.first()
            if mse:
                print(f"• {user.username}: {mse.first_name} {mse.last_name}")
                print(f"  Role: {mse.category.name}, Location: {mse.location}")
                print(f"  Status: {mse.status}")
        except:
            print(f"• {user.username}: MSE data not found")
    
    # Groups and Memberships
    print("\n👥 GROUPS & MEMBERSHIPS:")
    print("-" * 30)
    groups = Group.objects.all()
    for group in groups:
        memberships = group.memberships.filter(is_active=True)
        print(f"• {group.name}")
        print(f"  Description: {group.description}")
        print(f"  Members: {memberships.count()}")
        print(f"  Created by: {group.created_by.username if group.created_by else 'N/A'}")
    
    # Group Wallets
    print("\n💳 GROUP WALLETS:")
    print("-" * 30)
    group_wallets = GroupWallet.objects.all()
    total_group_balance = 0
    for wallet in group_wallets:
        print(f"• {wallet.group.name}: {wallet.balance} {wallet.currency}")
        total_group_balance += wallet.balance
    print(f"\nTotal group balance: {total_group_balance} UGX")
    
    # Loan Products
    print("\n🏦 LOAN PRODUCTS:")
    print("-" * 30)
    loan_products = LoanProduct.objects.all()
    for product in loan_products:
        print(f"• {product.name}")
        print(f"  Interest Rate: {product.interest_rate}%")
        print(f"  Max Amount: {product.max_amount} UGX")
        print(f"  Repayment Period: {product.repayment_period_months} months")
        print(f"  Active: {'Yes' if product.is_active else 'No'}")
    
    # Group Loans
    print("\n💰 GROUP LOANS:")
    print("-" * 30)
    group_loans = GroupLoan.objects.all()[:10]  # Show first 10
    for loan in group_loans:
        print(f"• {loan.group.name} - {loan.product.name}")
        print(f"  Amount: {loan.amount} UGX, Status: {loan.status.upper()}")
        print(f"  Created: {loan.created_at.strftime('%Y-%m-%d')}")
        if loan.approved_at:
            print(f"  Approved: {loan.approved_at.strftime('%Y-%m-%d')}")
        if loan.disbursed_at:
            print(f"  Disbursed: {loan.disbursed_at.strftime('%Y-%m-%d')}")
    
    print(f"\n... and {GroupLoan.objects.count() - 10} more loans")
    
    # Loan Repayments
    print("\n💸 LOAN REPAYMENTS:")
    print("-" * 30)
    repayments = GroupLoanRepayment.objects.all()[:10]  # Show first 10
    for repayment in repayments:
        print(f"• {repayment.loan.group.name} - {repayment.loan.product.name}")
        print(f"  Amount: {repayment.amount} UGX")
        print(f"  Repaid: {repayment.repaid_at.strftime('%Y-%m-%d')}")
    
    print(f"\n... and {GroupLoanRepayment.objects.count() - 10} more repayments")
    
    # Products
    print("\n🛍️ PRODUCTS:")
    print("-" * 30)
    products = Product.objects.all()
    for product in products:
        print(f"• {product.name}: {product.price} UGX per {product.unit}")
        print(f"  MSE: {product.mse.first_name} {product.mse.last_name}")
    
    # Transactions
    print("\n💰 TRANSACTIONS:")
    print("-" * 30)
    transactions = Transaction.objects.all()[:10]  # Show first 10
    for transaction in transactions:
        print(f"• {transaction.type.upper()}: {transaction.product.name}")
        print(f"  Amount: {transaction.amount} UGX, Qty: {transaction.quantity}")
        print(f"  MSE: {transaction.mse.first_name}, Date: {transaction.created_at.strftime('%Y-%m-%d')}")
    
    print(f"\n... and {Transaction.objects.count() - 10} more transactions")
    
    # Customers and Suppliers
    print("\n👥 CUSTOMERS:")
    print("-" * 30)
    customers = Customer.objects.all()[:5]
    for customer in customers:
        print(f"• {customer.name} ({customer.phone_number})")
        print(f"  MSE: {customer.mse.first_name}")
    
    print("\n🏢 SUPPLIERS:")
    print("-" * 30)
    suppliers = Supplier.objects.all()[:5]
    for supplier in suppliers:
        print(f"• {supplier.name} ({supplier.phone_number})")
        print(f"  MSE: {supplier.mse.first_name}")
    
    # Wallets
    print("\n💳 WALLETS:")
    print("-" * 30)
    wallets = Wallet.objects.all()
    total_balance = 0
    for wallet in wallets:
        print(f"• {wallet.mse.first_name}: {wallet.balance} {wallet.currency}")
        total_balance += wallet.balance
    print(f"\nTotal system balance: {total_balance} UGX")
    
    # Notifications
    print("\n🔔 NOTIFICATIONS:")
    print("-" * 30)
    notifications = Notification.objects.all()[:5]
    for notification in notifications:
        status = "✅ READ" if notification.is_read else "📬 UNREAD"
        print(f"• {status}: {notification.message}")
        print(f"  MSE: {notification.mse.first_name}, Date: {notification.created_at.strftime('%Y-%m-%d')}")
    
    print(f"\n... and {Notification.objects.count() - 5} more notifications")
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY:")
    print(f"• Total Users: {User.objects.count()}")
    print(f"• Total MSEs: {MSE.objects.count()}")
    print(f"• Total Groups: {Group.objects.count()}")
    print(f"• Total Group Memberships: {GroupMembership.objects.count()}")
    print(f"• Total Group Wallets: {GroupWallet.objects.count()}")
    print(f"• Total Loan Products: {LoanProduct.objects.count()}")
    print(f"• Total Group Loans: {GroupLoan.objects.count()}")
    print(f"• Total Loan Repayments: {GroupLoanRepayment.objects.count()}")
    print(f"• Total Products: {Product.objects.count()}")
    print(f"• Total Transactions: {Transaction.objects.count()}")
    print(f"• Total Customers: {Customer.objects.count()}")
    print(f"• Total Suppliers: {Supplier.objects.count()}")
    print(f"• Total Notifications: {Notification.objects.count()}")
    print(f"• Total Wallets: {Wallet.objects.count()}")
    print("=" * 60)


def view_api_endpoints():
    """Show available API endpoints for the data"""
    print("\n🌐 API ENDPOINTS FOR FRONTEND:")
    print("-" * 40)
    print("• /api/mse/ - List all MSEs")
    print("• /api/groups/ - List all groups")
    print("• /api/group-memberships/ - List group memberships")
    print("• /api/group-wallets/ - List group wallets")
    print("• /api/loan-products/ - List loan products")
    print("• /api/group-loans/ - List group loans")
    print("• /api/group-loan-repayments/ - List loan repayments")
    print("• /api/products/ - List all products")
    print("• /api/transactions/ - List all transactions")
    print("• /api/customers/ - List all customers")
    print("• /api/suppliers/ - List all suppliers")
    print("• /api/notifications/ - List all notifications")
    print("• /api/wallets/ - List all wallets")
    print("\nNote: You may need to configure these endpoints in your URLs")


if __name__ == '__main__':
    try:
        view_sample_data()
        view_api_endpoints()
    except Exception as e:
        print(f"Error viewing data: {str(e)}")
        sys.exit(1)
