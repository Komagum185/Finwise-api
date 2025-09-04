#!/usr/bin/env python3
"""
Script to migrate existing users from the old role system to the new flexible role system.
This script will:
1. Update existing users to use the new boolean role fields
2. Set appropriate capabilities based on their current roles
3. Preserve existing data and relationships

Run this script from the Django project root directory.
"""

import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'finwise.settings')
django.setup()

from authentication.models import CustomUser
from django.db import transaction

def migrate_user_roles():
    """Migrate existing users to the new flexible role system"""
    
    print("🚀 Starting role migration...")
    
    # Get all users
    users = CustomUser.objects.all()
    print(f"Found {users.count()} users to migrate")
    
    migrated_count = 0
    errors = []
    
    with transaction.atomic():
        for user in users:
            try:
                print(f"Migrating user: {user.username}")
                
                # Check if user already has new role fields populated
                if hasattr(user, 'is_super_admin') and any([user.is_super_admin, user.is_agent, user.is_mse, user.is_partner]):
                    print(f"  - User {user.username} already migrated, skipping")
                    continue
                
                # Get current role from old system
                old_role = getattr(user, 'role', None)
                old_rights = getattr(user, 'rights', None)
                
                print(f"  - Old role: {old_role}, Old rights: {old_rights}")
                
                # Set new role fields based on old role
                if old_role == 'super_admin':
                    user.is_super_admin = True
                    user.is_agent = False
                    user.is_mse = False
                    user.is_partner = False
                elif old_role == 'agent':
                    user.is_super_admin = False
                    user.is_agent = True
                    user.is_mse = False
                    user.is_partner = False
                elif old_role == 'mse':
                    user.is_super_admin = False
                    user.is_agent = False
                    user.is_mse = True
                    user.is_partner = False
                elif old_role == 'partner':
                    user.is_super_admin = False
                    user.is_agent = False
                    user.is_mse = False
                    user.is_partner = True
                else:
                    # Default to MSE if no role specified
                    user.is_super_admin = False
                    user.is_agent = False
                    user.is_mse = True
                    user.is_partner = False
                
                # Set capabilities based on roles
                capabilities = []
                
                if user.is_super_admin:
                    capabilities.extend([
                        'can_manage_users',
                        'can_manage_mse', 
                        'can_view_reports',
                        'can_export_data',
                        'can_approve_loans',
                        'can_manage_wallets',
                        'can_access_admin_dashboard',
                        'can_access_agent_dashboard',
                        'can_access_mse_dashboard',
                        'can_access_partner_dashboard',
                        # MSE Business Operations (super admin can do everything)
                        'can_manage_products',
                        'can_manage_inventory',
                        'can_manage_customers',
                        'can_manage_suppliers',
                        'can_manage_transactions',
                        'can_view_market_data',
                        'can_manage_loans',
                        'can_manage_wallet'
                    ])
                elif user.is_agent:
                    capabilities.extend([
                        'can_manage_mse',
                        'can_view_reports',
                        'can_export_data',
                        'can_approve_loans',
                        'can_manage_wallets',
                        'can_access_agent_dashboard',
                        # Agents can view MSE business data
                        'can_view_market_data',
                        'can_view_mse_products',
                        'can_view_mse_inventory'
                    ])
                elif user.is_mse:
                    capabilities.extend([
                        'can_view_reports',
                        'can_export_data',
                        'can_access_mse_dashboard',
                        # MSE Business Operations - they can manage their own business
                        'can_manage_products',
                        'can_manage_inventory',
                        'can_manage_customers',
                        'can_manage_suppliers',
                        'can_manage_transactions',
                        'can_view_market_data',
                        'can_manage_loans',
                        'can_manage_wallet'
                    ])
                elif user.is_partner:
                    capabilities.extend([
                        'can_view_reports',
                        'can_export_data',
                        'can_access_partner_dashboard',
                        # Partners can view market data and MSE performance
                        'can_view_market_data',
                        'can_view_mse_products',
                        'can_view_mse_inventory'
                    ])
                
                # Add export capability if user had export rights
                if old_rights == 'export':
                    if 'can_export_data' not in capabilities:
                        capabilities.append('can_export_data')
                
                # Set capabilities
                user.capabilities = capabilities
                
                # Save user
                user.save()
                
                print(f"  ✅ Successfully migrated {user.username}")
                migrated_count += 1
                
            except Exception as e:
                error_msg = f"Error migrating user {user.username}: {str(e)}"
                print(f"  ❌ {error_msg}")
                errors.append(error_msg)
    
    print(f"\n🎉 Migration completed!")
    print(f"Successfully migrated: {migrated_count} users")
    
    if errors:
        print(f"Errors encountered: {len(errors)}")
        for error in errors:
            print(f"  - {error}")
    else:
        print("No errors encountered!")
    
    return migrated_count, errors

def verify_migration():
    """Verify that the migration was successful"""
    
    print("\n🔍 Verifying migration...")
    
    users = CustomUser.objects.all()
    verified_count = 0
    
    for user in users:
        try:
            # Check if user has new role fields
            if not hasattr(user, 'is_super_admin'):
                print(f"❌ User {user.username} missing new role fields")
                continue
            
            # Check if user has at least one role
            if not any([user.is_super_admin, user.is_agent, user.is_mse, user.is_partner]):
                print(f"❌ User {user.username} has no roles assigned")
                continue
            
            # Check if user has capabilities
            if not hasattr(user, 'capabilities') or not user.capabilities:
                print(f"❌ User {user.username} has no capabilities")
                continue
            
            print(f"✅ User {user.username} properly migrated")
            verified_count += 1
            
        except Exception as e:
            print(f"❌ Error verifying user {user.username}: {str(e)}")
    
    print(f"\nVerification complete: {verified_count}/{users.count()} users properly migrated")
    return verified_count == users.count()

if __name__ == "__main__":
    print("🔄 Starting user role migration...")
    
    # Run migration
    migrated_count, errors = migrate_user_roles()
    
    # Verify migration
    if migrated_count > 0:
        success = verify_migration()
        if success:
            print("\n🎉 All users successfully migrated to the new flexible role system!")
        else:
            print("\n⚠️  Migration completed but some users may have issues")
    else:
        print("\nℹ️  No users were migrated (possibly already migrated)")
    
    print("\nMigration script completed!")
