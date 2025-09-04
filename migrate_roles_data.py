#!/usr/bin/env python3
"""
Script to migrate user role data from old fields to new flexible role fields.
This script reads the old role/rights data directly from the database and sets
the appropriate new boolean role fields and capabilities.
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
from django.db import transaction, connection

def migrate_role_data():
    """Migrate role data from old fields to new flexible role fields"""
    
    print("🚀 Starting role data migration...")
    
    # Get all users with their old role data from database
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id, username, role, rights 
            FROM authentication_customuser 
            ORDER BY username
        """)
        users_data = cursor.fetchall()
    
    print(f"Found {len(users_data)} users to migrate")
    
    migrated_count = 0
    errors = []
    
    with transaction.atomic():
        for user_id, username, old_role, old_rights in users_data:
            try:
                print(f"Migrating user: {username}")
                print(f"  - Old role: {old_role}, Old rights: {old_rights}")
                
                # Get the user object
                user = CustomUser.objects.get(id=user_id)
                
                # Reset all role fields
                user.is_super_admin = False
                user.is_agent = False
                user.is_mse = False
                user.is_partner = False
                
                # Set new role fields based on old role
                if old_role == 'admin' or old_role == 'super_admin':
                    user.is_super_admin = True
                    print(f"  - Set as Super Admin")
                elif old_role == 'agent':
                    user.is_agent = True
                    print(f"  - Set as Agent")
                elif old_role == 'mse':
                    user.is_mse = True
                    print(f"  - Set as MSE")
                elif old_role == 'partner':
                    user.is_partner = True
                    print(f"  - Set as Partner")
                else:
                    # Default to MSE if no role specified
                    user.is_mse = True
                    print(f"  - Set as MSE (default)")
                
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
                    print(f"  - Added export capability")
                
                # Set capabilities
                user.capabilities = capabilities
                
                # Save user
                user.save()
                
                print(f"  ✅ Successfully migrated {username}")
                migrated_count += 1
                
            except Exception as e:
                error_msg = f"Error migrating user {username}: {str(e)}"
                print(f"  ❌ {error_msg}")
                errors.append(error_msg)
    
    print(f"\n🎉 Role data migration completed!")
    print(f"Successfully migrated: {migrated_count} users")
    
    if errors:
        print(f"Errors encountered: {len(errors)}")
        for error in errors:
            print(f"  - {error}")
    else:
        print("No errors encountered!")
    
    return migrated_count, errors

def verify_migration():
    """Verify that the role data migration was successful"""
    
    print("\n🔍 Verifying role data migration...")
    
    users = CustomUser.objects.all()
    verified_count = 0
    
    for user in users:
        try:
            # Check if user has at least one role
            if not any([user.is_super_admin, user.is_agent, user.is_mse, user.is_partner]):
                print(f"❌ User {user.username} has no roles assigned")
                continue
            
            # Check if user has capabilities
            if not user.capabilities:
                print(f"❌ User {user.username} has no capabilities")
                continue
            
            # Show user's roles and capabilities count
            roles = []
            if user.is_super_admin:
                roles.append('Super Admin')
            if user.is_agent:
                roles.append('Agent')
            if user.is_mse:
                roles.append('MSE')
            if user.is_partner:
                roles.append('Partner')
            
            role_str = ', '.join(roles)
            print(f"✅ User {user.username}: {role_str} ({len(user.capabilities)} capabilities)")
            verified_count += 1
            
        except Exception as e:
            print(f"❌ Error verifying user {user.username}: {str(e)}")
    
    print(f"\nVerification complete: {verified_count}/{users.count()} users properly migrated")
    return verified_count == users.count()

if __name__ == "__main__":
    print("🔄 Starting user role data migration...")
    
    # Run migration
    migrated_count, errors = migrate_role_data()
    
    # Verify migration
    if migrated_count > 0:
        success = verify_migration()
        if success:
            print("\n🎉 All users successfully migrated to the new flexible role system!")
        else:
            print("\n⚠️  Migration completed but some users may have issues")
    else:
        print("\nℹ️  No users were migrated (possibly already migrated)")
    
    print("\nRole data migration script completed!")
