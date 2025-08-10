#!/usr/bin/env python3
"""
Script to create default categories and sample data for the Finwise API
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'finwise.settings')
django.setup()

from api.models import Category

def create_default_categories():
    """Create default categories for the financial app"""
    
    # Income categories
    income_categories = [
        {'name': 'Salary', 'description': 'Regular employment income', 'category_type': 'income', 'icon': '💰', 'color': '#28a745'},
        {'name': 'Freelance', 'description': 'Freelance or contract work', 'category_type': 'income', 'icon': '💼', 'color': '#17a2b8'},
        {'name': 'Investment', 'description': 'Investment returns and dividends', 'category_type': 'income', 'icon': '📈', 'color': '#ffc107'},
        {'name': 'Business', 'description': 'Business income', 'category_type': 'income', 'icon': '🏢', 'color': '#6f42c1'},
        {'name': 'Other Income', 'description': 'Other sources of income', 'category_type': 'income', 'icon': '➕', 'color': '#20c997'},
    ]
    
    # Expense categories
    expense_categories = [
        {'name': 'Food & Dining', 'description': 'Groceries, restaurants, and food delivery', 'category_type': 'expense', 'icon': '🍽️', 'color': '#dc3545'},
        {'name': 'Transportation', 'description': 'Gas, public transport, rideshare', 'category_type': 'expense', 'icon': '🚗', 'color': '#fd7e14'},
        {'name': 'Housing', 'description': 'Rent, mortgage, utilities', 'category_type': 'expense', 'icon': '🏠', 'color': '#6f42c1'},
        {'name': 'Entertainment', 'description': 'Movies, games, hobbies', 'category_type': 'expense', 'icon': '🎬', 'color': '#e83e8c'},
        {'name': 'Shopping', 'description': 'Clothing, electronics, general shopping', 'category_type': 'expense', 'icon': '🛍️', 'color': '#fd7e14'},
        {'name': 'Healthcare', 'description': 'Medical expenses, insurance', 'category_type': 'expense', 'icon': '🏥', 'color': '#dc3545'},
        {'name': 'Education', 'description': 'Tuition, books, courses', 'category_type': 'expense', 'icon': '📚', 'color': '#17a2b8'},
        {'name': 'Travel', 'description': 'Vacations, business trips', 'category_type': 'expense', 'icon': '✈️', 'color': '#20c997'},
        {'name': 'Utilities', 'description': 'Electricity, water, internet, phone', 'category_type': 'expense', 'icon': '⚡', 'color': '#ffc107'},
        {'name': 'Insurance', 'description': 'Car, home, life insurance', 'category_type': 'expense', 'icon': '🛡️', 'color': '#6c757d'},
        {'name': 'Debt Payment', 'description': 'Credit cards, loans', 'category_type': 'expense', 'icon': '💳', 'color': '#dc3545'},
        {'name': 'Savings', 'description': 'Emergency fund, investments', 'category_type': 'expense', 'icon': '💰', 'color': '#28a745'},
        {'name': 'Other Expenses', 'description': 'Miscellaneous expenses', 'category_type': 'expense', 'icon': '📝', 'color': '#6c757d'},
    ]
    
    # Create categories
    created_count = 0
    for category_data in income_categories + expense_categories:
        category, created = Category.objects.get_or_create(
            name=category_data['name'],
            defaults=category_data
        )
        if created:
            created_count += 1
            print(f"Created category: {category.name}")
        else:
            print(f"Category already exists: {category.name}")
    
    print(f"\nTotal categories created: {created_count}")
    print(f"Total categories in database: {Category.objects.count()}")

if __name__ == "__main__":
    print("Creating default categories...")
    create_default_categories()
    print("Done!") 