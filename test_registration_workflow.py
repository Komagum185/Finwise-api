#!/usr/bin/env python3
"""
Test script for the new registration approval workflow and OTP functionality
"""

import requests
import json
import time

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api"
AUTH_BASE = f"{BASE_URL}/api/auth"

def test_registration_workflow():
    """Test the complete registration approval workflow"""
    
    print("=== Testing Registration Approval Workflow ===\n")
    
    # 1. Create a pending registration
    print("1. Creating pending registration...")
    registration_data = {
        "username": "testuser123",
        "email": "testuser123@example.com",
        "password": "SecurePass123!",
        "password_confirm": "SecurePass123!",
        "first_name": "Test",
        "last_name": "User",
        "phone_number": "+1234567890",
        "default_currency": "USD",
        "monthly_income": "5000.00"
    }
    
    response = requests.post(f"{AUTH_BASE}/register-with-approval/", json=registration_data)
    print(f"Status: {response.status_code}")
    if response.status_code == 201:
        data = response.json()
        registration_id = data['registration_id']
        print(f"Registration ID: {registration_id}")
        print(f"Message: {data['message']}")
    else:
        print(f"Error: {response.text}")
        return
    
    print("\n2. Verifying OTP...")
    # In a real scenario, the user would receive the OTP via email
    # For testing, we'll get it from the logs or database
    # For now, let's assume the OTP is "123456" (you'll need to check the logs)
    
    otp_data = {
        "otp_code": "123456",  # Replace with actual OTP from logs
        "purpose": "email_verification",
        "registration_id": registration_id
    }
    
    response = requests.post(f"{AUTH_BASE}/verify-otp/", json=otp_data)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print(f"Message: {response.json()['message']}")
    else:
        print(f"Error: {response.text}")
        print("Note: Check the server logs for the actual OTP code")
    
    print("\n3. Admin viewing pending registrations...")
    # This would require admin authentication
    # For testing, we'll just show the endpoint
    print("GET /api/auth/pending-registrations/ (requires admin auth)")
    
    print("\n4. Admin approving registration...")
    # This would require admin authentication
    approve_data = {
        "registration_id": registration_id
    }
    print(f"POST /api/auth/pending-registrations/{registration_id}/approve/ (requires admin auth)")
    
    print("\n5. User setting password after approval...")
    # After approval, user would receive an OTP for password setup
    password_otp_data = {
        "otp_code": "654321",  # Replace with actual OTP from logs
        "purpose": "password_reset",
        "user_id": "user_id_here",  # Replace with actual user ID
        "new_password": "NewSecurePass123!"
    }
    print(f"POST /api/auth/verify-otp/ with password reset data")
    
    print("\n=== Workflow Complete ===")


def test_otp_functionality():
    """Test OTP verification and resend functionality"""
    
    print("\n=== Testing OTP Functionality ===\n")
    
    # Test resending OTP
    print("1. Resending OTP...")
    resend_data = {
        "purpose": "email_verification",
        "registration_id": "registration_id_here"  # Replace with actual ID
    }
    
    response = requests.post(f"{AUTH_BASE}/resend-otp/", json=resend_data)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print(f"Message: {response.json()['message']}")
    else:
        print(f"Error: {response.text}")
    
    print("\n2. Verifying OTP...")
    verify_data = {
        "otp_code": "123456",  # Replace with actual OTP
        "purpose": "email_verification",
        "registration_id": "registration_id_here"  # Replace with actual ID
    }
    
    response = requests.post(f"{AUTH_BASE}/verify-otp/", json=verify_data)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print(f"Message: {response.json()['message']}")
    else:
        print(f"Error: {response.text}")


def test_user_otp():
    """Test OTP functionality for existing users"""
    
    print("\n=== Testing User OTP Functionality ===\n")
    
    # Test resending OTP for existing user
    print("1. Resending OTP for existing user...")
    resend_data = {
        "purpose": "password_reset",
        "user_id": "user_id_here"  # Replace with actual user ID
    }
    
    response = requests.post(f"{AUTH_BASE}/resend-otp/", json=resend_data)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print(f"Message: {response.json()['message']}")
    else:
        print(f"Error: {response.text}")
    
    print("\n2. Verifying OTP for existing user...")
    verify_data = {
        "otp_code": "123456",  # Replace with actual OTP
        "purpose": "password_reset",
        "user_id": "user_id_here",  # Replace with actual user ID
        "new_password": "NewSecurePass123!"
    }
    
    response = requests.post(f"{AUTH_BASE}/verify-otp/", json=verify_data)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print(f"Message: {response.json()['message']}")
    else:
        print(f"Error: {response.text}")


if __name__ == "__main__":
    print("Finwise API - Registration Approval Workflow Test")
    print("=" * 50)
    
    try:
        test_registration_workflow()
        test_otp_functionality()
        test_user_otp()
    except requests.exceptions.ConnectionError:
        print("\nError: Could not connect to the server.")
        print("Make sure the Django server is running on http://localhost:8000")
    except Exception as e:
        print(f"\nError: {str(e)}")
    
    print("\nTest completed!")
    print("\nNote: To see actual OTP codes, check the Django server logs.")
    print("The OTP codes are logged for testing purposes.") 