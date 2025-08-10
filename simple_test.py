#!/usr/bin/env python3
"""
Simple test script to demonstrate the registration approval workflow
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:8000"
AUTH_BASE = f"{BASE_URL}/api/auth"

def test_registration():
    """Test the registration with approval workflow"""
    
    print("=== Testing Registration Approval Workflow ===\n")
    
    # 1. Create a pending registration
    print("1. Creating pending registration...")
    registration_data = {
        "username": "testuser789",
        "email": "test789@example.com",
        "password": "SecurePass123!",
        "password_confirm": "SecurePass123!",
        "first_name": "Test",
        "last_name": "User",
        "phone_number": "+1234567890",
        "default_currency": "USD",
        "monthly_income": "5000.00"
    }
    
    try:
        response = requests.post(f"{AUTH_BASE}/register-with-approval/", json=registration_data)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 201:
            data = response.json()
            registration_id = data['registration_id']
            print(f"✅ Registration created successfully!")
            print(f"   Registration ID: {registration_id}")
            print(f"   Message: {data['message']}")
            return registration_id
        else:
            print(f"❌ Error: {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to the server.")
        print("   Make sure the Django server is running on http://localhost:8000")
        return None
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None


def test_otp_verification(registration_id):
    """Test OTP verification (with dummy OTP)"""
    
    print(f"\n2. Testing OTP verification...")
    
    otp_data = {
        "otp_code": "123456",  # This will fail - check server logs for actual OTP
        "purpose": "email_verification",
        "registration_id": registration_id
    }
    
    try:
        response = requests.post(f"{AUTH_BASE}/verify-otp/", json=otp_data)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ OTP verified successfully!")
            print(f"   Message: {response.json()['message']}")
        else:
            print("❌ OTP verification failed (expected with dummy OTP)")
            print(f"   Error: {response.text}")
            print("   Note: Check server logs for actual OTP code")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")


def test_resend_otp(registration_id):
    """Test resending OTP"""
    
    print(f"\n3. Testing OTP resend...")
    
    resend_data = {
        "purpose": "email_verification",
        "registration_id": registration_id
    }
    
    try:
        response = requests.post(f"{AUTH_BASE}/resend-otp/", json=resend_data)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ OTP resent successfully!")
            print(f"   Message: {response.json()['message']}")
            print("   Note: Check server logs for the new OTP code")
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")


def show_admin_endpoints(registration_id):
    """Show the admin endpoints that would be used"""
    
    print(f"\n4. Admin Workflow Endpoints:")
    print("   (These require admin authentication)")
    print(f"   • GET {AUTH_BASE}/pending-registrations/")
    print(f"   • POST {AUTH_BASE}/pending-registrations/{registration_id}/approve/")
    print(f"   • POST {AUTH_BASE}/pending-registrations/{registration_id}/reject/")


def main():
    print("Finwise API - Registration Approval Workflow Test")
    print("=" * 60)
    
    # Test registration
    registration_id = test_registration()
    
    if registration_id:
        # Test OTP verification
        test_otp_verification(registration_id)
        
        # Test resend OTP
        test_resend_otp(registration_id)
        
        # Show admin endpoints
        show_admin_endpoints(registration_id)
    
    print("\n" + "=" * 60)
    print("Test completed!")
    print("\nNotes:")
    print("• OTP codes are logged to the Django server console")
    print("• Admin endpoints require authentication with admin privileges")
    print("• Replace utility functions in users/utils.py with actual email/SMS services")


if __name__ == "__main__":
    main() 