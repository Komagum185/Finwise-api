#!/usr/bin/env python3
"""
Script to create a partner user for testing the partner dashboard API.
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

User = get_user_model()


def create_partner_users():
    """Create partner users for testing"""
    
    # Create partner viewer user
    partner_viewer, created = User.objects.get_or_create(
        username='partner_viewer',
        defaults={
            'first_name': 'Partner',
            'last_name': 'Viewer',
            'phone_number': '+256700000001',
            'NIN': 'PARTNER123456789',
            'role': 'partner',
            'rights': 'viewer',
            'email': 'partner.viewer@example.com',
            'is_approved': True
        }
    )
    
    if created:
        partner_viewer.set_password('password123')
        partner_viewer.save()
        print(f'Created partner viewer user: {partner_viewer.username}')
    else:
        print(f'Partner viewer user already exists: {partner_viewer.username}')
    
    # Create partner export user
    partner_export, created = User.objects.get_or_create(
        username='partner_export',
        defaults={
            'first_name': 'Partner',
            'last_name': 'Export',
            'phone_number': '+256700000002',
            'NIN': 'PARTNER123456790',
            'role': 'partner',
            'rights': 'export',
            'email': 'partner.export@example.com',
            'is_approved': True
        }
    )
    
    if created:
        partner_export.set_password('password123')
        partner_export.save()
        print(f'Created partner export user: {partner_export.username}')
    else:
        print(f'Partner export user already exists: {partner_export.username}')
    
    print("\nPartner users created successfully!")
    print("You can now test the partner dashboard API with these credentials:")
    print("Partner Viewer: username=partner_viewer, password=password123")
    print("Partner Export: username=partner_export, password=password123")


if __name__ == '__main__':
    create_partner_users()
